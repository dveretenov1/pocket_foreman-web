from anthropic import Anthropic
from dotenv import load_dotenv
import os

def chat_with_claude():
    # Load environment variables
    load_dotenv()
    
    # Initialize Anthropic client
    anthropic = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    
    print("Chat with Claude (type 'exit' to end)")
    
    while True:
        # Get user input
        user_input = input("\nYou: ")
        if user_input.lower() == 'exit':
            break
            
        try:
            # Create a streaming message
            message = anthropic.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1024,
                temperature=0.7,
                stream=True,
                messages=[{
                    "role": "user",
                    "content": user_input
                }]
            )
            
            # Print the streaming response
            print("\nClaude: ", end="", flush=True)
            for chunk in message:
                if chunk.type == "content_block_delta":
                    print(chunk.delta.text, end="", flush=True)
            print()  # New line after response
            
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    chat_with_claude()