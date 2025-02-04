import anthropic
import base64
import os
from pathlib import Path
from dotenv import load_dotenv
import textwrap
import shutil
import time
import sys
from typing import List, Dict, Any
import asyncio
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

def encode_pdf_to_base64(pdf_path: str) -> str:
    """Convert PDF file to base64 string"""
    with open(pdf_path, "rb") as pdf_file:
        return base64.b64encode(pdf_file.read()).decode('utf-8')

def check_pdf_size(pdf_path: str) -> bool:
    """Check if PDF file size is within limits"""
    max_size = 32 * 1024 * 1024  # 32MB
    return os.path.getsize(pdf_path) <= max_size

def get_valid_input(prompt: str) -> str:
    """Get user input and ensure it's not empty"""
    while True:
        try:
            user_input = input(prompt).strip()
            if user_input:
                return user_input
        except EOFError:
            continue

class ConsoleFormatter:
    def __init__(self):
        self.terminal_width = shutil.get_terminal_size().columns if hasattr(shutil, 'get_terminal_size') else 80
        self.indent = 2
        self.wrap_width = self.terminal_width - (self.indent * 2)
        self.current_line = " " * self.indent
        self.current_word = ""

    def print_user_message(self, message: str):
        """Format and print user message"""
        print("\n\033[1m🧑 Human:\033[0m")
        wrapped_text = textwrap.fill(
            message, 
            width=self.wrap_width,
            initial_indent=" " * self.indent,
            subsequent_indent=" " * self.indent
        )
        print(wrapped_text)

    def print_chunk(self, chunk: str):
        """Print a chunk of text with proper word wrapping"""
        for char in chunk:
            if char.isspace():
                if len(self.current_line) + len(self.current_word) > self.wrap_width:
                    print(self.current_line)
                    self.current_line = " " * self.indent + self.current_word + char
                else:
                    self.current_line += self.current_word + char
                self.current_word = ""
            else:
                self.current_word += char
            
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(0.01)  # Adjust streaming speed here

    def flush_text(self):
        """Flush any remaining text"""
        if self.current_word:
            if len(self.current_line) + len(self.current_word) > self.wrap_width:
                print(self.current_line)
                print(" " * self.indent + self.current_word)
            else:
                print(self.current_line + self.current_word)
        self.current_line = " " * self.indent
        self.current_word = ""
        print()  # Add final newline

    def print_assistant_start(self):
        """Print assistant message header"""
        print("\n\033[1m🤖 Assistant:\033[0m")
        self._animate_typing()

    def _animate_typing(self):
        """Show a brief typing animation"""
        for _ in range(2):
            print(" " * self.indent + ".", end="", flush=True)
            time.sleep(0.15)
            print(".", end="", flush=True)
            time.sleep(0.15)
            print(".", end="", flush=True)
            time.sleep(0.15)
            print("\r" + " " * (self.indent + 3), end="\r", flush=True)

    def print_separator(self):
        """Print a separator line"""
        print("\n" + "─" * self.terminal_width + "\n")

    def print_error(self, error_message: str):
        """Format and print error messages"""
        print(f"\n\033[91mError:\033[0m {error_message}")

    def print_token_usage(self, input_tokens: int, output_tokens: int, total_tokens: int, cost: float):
        """Format and print token usage information"""
        print("\n\033[90mToken usage:")
        print(f"  Input tokens:     {input_tokens:,}")
        print(f"  Output tokens:    {output_tokens:,}")
        print(f"  Total tokens:     {total_tokens:,}")
        print(f"  Estimated cost:   ${cost:.6f}\033[0m")

class PDFAnalyzer:
    def __init__(self, api_key: str, pdf_files: List[str]):
        self.client = anthropic.Client(
            api_key=api_key
        )
        self.pdf_files = pdf_files
        self.system_prompt = """You are an expert construction assistant helping analyze building plans. When analyzing plans or answering questions:
1. Reference specific sections/pages of the plans
2. State measurements in both metric and imperial units
3. If unsure about details, ask for clarification
4. Highlight any safety or code implications
5. Consider practical implementation aspects"""
        self.pdf_content = self._load_pdfs()
        self.conversation_context = []
        self.formatter = ConsoleFormatter()

    def _load_pdfs(self) -> List[Dict]:
        """Load all PDFs into memory"""
        pdf_content = []
        for pdf_file in self.pdf_files:
            if os.path.exists(pdf_file):
                pdf_content.append({
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": encode_pdf_to_base64(pdf_file)
                    }
                })
        return pdf_content

    async def analyze_pdfs(self) -> Dict:
        """Perform initial PDF analysis with streaming"""
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": "Please review these plans and identify the key systems and components."},
                *self.pdf_content
            ]
        }]

        try:
            stream = await self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                temperature=0,
                system=self.system_prompt,
                messages=messages,
                stream=True
            )
            
            self.formatter.print_assistant_start()
            response_text = ""

            async for chunk in stream:
                if hasattr(chunk, 'delta') and hasattr(chunk.delta, 'text'):
                    response_text += chunk.delta.text
                    self.formatter.print_chunk(chunk.delta.text)
            
            self.formatter.flush_text()

            return {
                'response': response_text,
                'token_usage': {
                    'input_tokens': stream.usage.input_tokens,
                    'output_tokens': stream.usage.output_tokens
                }
            }

        except Exception as e:
            raise Exception(f"Error analyzing PDFs: {str(e)}")

    async def get_response(self, question: str) -> Dict:
        """Get streaming response for a follow-up question"""
        recent_context = self.conversation_context[-4:] if self.conversation_context else []
        
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": "Reference these plans to answer the following question:"},
                *self.pdf_content
            ]
        }]
        messages.extend(recent_context)
        messages.append({
            "role": "user",
            "content": [{"type": "text", "text": question}]
        })

        try:
            stream = await self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                temperature=0,
                messages=messages,
                stream=True
            )

            self.formatter.print_assistant_start()
            response_text = ""
            
            async for chunk in stream:
                if hasattr(chunk, 'delta') and hasattr(chunk.delta, 'text'):
                    response_text += chunk.delta.text
                    self.formatter.print_chunk(chunk.delta.text)
            
            self.formatter.flush_text()

            # Update conversation context
            self.conversation_context.extend([
                {"role": "user", "content": [{"type": "text", "text": question}]},
                {"role": "assistant", "content": [{"type": "text", "text": response_text}]}
            ])

            return {
                'response': response_text,
                'token_usage': {
                    'input_tokens': stream.usage.input_tokens,
                    'output_tokens': stream.usage.output_tokens
                }
            }

        except Exception as e:
            raise Exception(f"Error getting response: {str(e)}")

async def main():
    formatter = ConsoleFormatter()
    
    # Print header with current date/time
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n\033[1m╔═══════════════════════════════════════════════════════╗")
    print(f"║  Construction Plans Analysis Assistant - {current_time}  ║")
    print(f"╚═══════════════════════════════════════════════════════╝\033[0m")
    
    # Check environment and files
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        formatter.print_error("ANTHROPIC_API_KEY not found in environment variables")
        return

    # Get PDF file path from user or use default
    default_pdf = "Mechanical Only.pdf"
    pdf_path = input(f"\nEnter PDF file path (press Enter for default '{default_pdf}'): ").strip() or default_pdf
    pdf_files = [pdf_path]
    
    # Validate PDF files
    for pdf_file in pdf_files:
        if not os.path.exists(pdf_file):
            formatter.print_error(f"PDF file not found: {pdf_file}")
            return
        if not check_pdf_size(pdf_file):
            formatter.print_error(f"PDF file exceeds 32MB limit: {pdf_file}")
            return

    try:
        analyzer = PDFAnalyzer(api_key, pdf_files)
        
        print("\nAnalyzing plans, please wait...")
        result = await analyzer.analyze_pdfs()
        
        formatter.print_token_usage(
            result['token_usage']['input_tokens'],
            result['token_usage']['output_tokens'],
            sum(result['token_usage'].values()),
            (result['token_usage']['input_tokens'] * 0.00000163) + 
            (result['token_usage']['output_tokens'] * 0.00000551)
        )
        formatter.print_separator()

        while True:
            try:
                question = get_valid_input("\033[1mEnter your question about the plans (or 'quit' to exit):\033[0m ")
                if question.lower() == 'quit':
                    print("\nThank you for using the Construction Plans Analysis Assistant!")
                    break

                formatter.print_user_message(question)
                
                result = await analyzer.get_response(question)
                
                formatter.print_token_usage(
                    result['token_usage']['input_tokens'],
                    result['token_usage']['output_tokens'],
                    sum(result['token_usage'].values()),
                    (result['token_usage']['input_tokens'] * 0.00000163) + 
                    (result['token_usage']['output_tokens'] * 0.00000551)
                )
                formatter.print_separator()

            except KeyboardInterrupt:
                print("\n\nExiting gracefully...")
                break
            except Exception as e:
                formatter.print_error(str(e))

    except Exception as e:
        formatter.print_error(str(e))

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nExiting gracefully...")
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")