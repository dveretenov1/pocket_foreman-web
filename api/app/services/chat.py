# app/services/chat.py
from sqlalchemy.orm import Session
from fastapi import HTTPException
from ..models.chat import Chat
from ..models.message import Message
from ..models.file import File
from ..models.chat_files import ChatFile
from datetime import datetime
from typing import List, Optional, AsyncGenerator, Dict
from anthropic import Anthropic
from .s3 import s3_service
from ..config import get_settings
import json
import logging
import base64
from .billing.usage import usage_service
from .billing.token_conversion import token_conversion
from .billing.subscription import subscription_service
from ..models.subscription import SubscriptionTier

logger = logging.getLogger(__name__)
settings = get_settings()

class ChatService:
    def __init__(self):
        self.anthropic = Anthropic(
            api_key=settings.ANTHROPIC_API_KEY,
            default_headers={
                "anthropic-beta": "pdfs-2024-09-25",
                "anthropic-version": "2023-06-01"
            }
        )
        self.s3 = s3_service.s3
        self.bucket_name = s3_service.bucket_name

    async def create_chat(self, db: Session, user_id: str, title: str) -> Chat:
        try:
            db_chat = Chat(user_id=user_id, title=title)
            db.add(db_chat)
            db.commit()
            db.refresh(db_chat)
            return db_chat
        except Exception as e:
            logger.error(f"Error creating chat: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to create chat")

    async def update_chat_title(self, db: Session, chat_id: int, title: str, user_id: str) -> Chat:
        chat = db.query(Chat).filter(
            Chat.id == chat_id,
            Chat.user_id == user_id,
            Chat.deleted == False
        ).first()
        
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        
        chat.title = title
        chat.updated_at = datetime.now()
        db.commit()
        db.refresh(chat)
        return chat

    async def get_chat_files(self, db: Session, chat_id: int, user_id: str) -> List[File]:
        chat = db.query(Chat).filter(
            Chat.id == chat_id,
            Chat.user_id == user_id,
            Chat.deleted == False
        ).first()
        
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        
        files = db.query(File).join(ChatFile).filter(
            ChatFile.chat_id == chat_id,
            ChatFile.active == True,
            File.deleted == False
        ).all()
        
        return files

    async def get_chat_context(self, db: Session, chat_id: int) -> List[Dict]:
        """Get previous messages as context"""
        # Get messages with their associated files
        messages = db.query(Message).filter(
            Message.chat_id == chat_id,
            Message.deleted == False
        ).order_by(Message.created_at.asc()).all()
        
        # Get active files for this chat
        active_files = db.query(File).join(ChatFile).filter(
            ChatFile.chat_id == chat_id,
            ChatFile.active == True,
            File.deleted == False
        ).all()

        context = []
        
        # Add files as context if they exist
        if active_files:
            file_contents = []
            for file in active_files:
                try:
                    media_type = "application/pdf" if file.original_name.lower().endswith('.pdf') else "text/plain"
                    file_content = await self.get_file_content(file.s3_key, media_type)
                    file_contents.append(file_content)
                except Exception as e:
                    logger.error(f"Error reading file content: {str(e)}")
            
            if file_contents:
                context.append({
                    "role": "user",
                    "content": file_contents + [{"type": "text", "text": "Here are the relevant documents for our conversation."}]
                })

        # Add message history
        for msg in messages:
            if msg.content.strip():
                context.append({
                    "role": msg.role,
                    "content": msg.content
                })

        return context

    async def get_file_content(self, s3_key: str, file_type: str) -> Dict:
        """Get file content in the format required by Anthropic"""
        try:
            response = self.s3.get_object(Bucket=self.bucket_name, Key=s3_key)
            file_content = response['Body'].read()
            
            # Convert to base64
            base64_content = base64.b64encode(file_content).decode('utf-8')
            
            return {
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": file_type,
                    "data": base64_content
                }
            }
        except Exception as e:
            logger.error(f"Error reading file from S3: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to read file content")

    async def send_message(
        self,
        db: Session,
        chat_id: int,
        content: str,
        user_id: str,
        files: Optional[List[File]] = None
    ) -> AsyncGenerator[str, None]:
        try:
            # Calculate potential usage from this message
            estimated_input_tokens = len(content.split())
            # Estimate output tokens (typically 2-3x input, using 2.5x to be safe)
            estimated_output_tokens = int(estimated_input_tokens * 2.5)
            
            # Calculate potential PFT
            potential_pft = token_conversion.calculate_pft(
                input_tokens=estimated_input_tokens,
                output_tokens=estimated_output_tokens,
                storage_bytes=0
            )['total_pft']
            
            # Get current usage and subscription
            current_usage = await usage_service.get_current_usage(db, user_id)
            subscription = await subscription_service.get_user_subscription(db, user_id)
            
            # Default to free tier limit if no subscription
            monthly_limit = 10000  # Free tier PFT limit
            if subscription:
                tier = db.query(SubscriptionTier).get(subscription.tier_id)
                if tier:
                    monthly_limit = tier.monthly_pft
            
            # Check if this message would exceed the limit
            if current_usage['total_pft'] + potential_pft > monthly_limit:
                error_msg = 'This message would exceed your monthly token limit. Please upgrade your subscription to continue.'
                logger.warning(f"User {user_id} would exceed token limit: {current_usage['total_pft']} + {potential_pft} > {monthly_limit}")
                yield f"data: {json.dumps({'error': error_msg, 'done': True})}\n\n"
                return

            # Add content validation
            if not content or not content.strip():
                yield f"data: {json.dumps({'error': 'Message content cannot be empty', 'done': True})}\n\n"
                return

            # Get chat and verify access
            chat = db.query(Chat).filter(
                Chat.id == chat_id,
                Chat.user_id == user_id,
                Chat.deleted == False
            ).first()
            
            if not chat:
                yield f"data: {json.dumps({'error': 'Chat not found', 'done': True})}\n\n"
                return

            # Create user message
            user_message = Message(
                chat_id=chat_id,
                content=content,
                role="user"
            )
            db.add(user_message)
            db.commit()

            # Record user message usage
            try:
                input_tokens = len(content.split())
                logger.info(f"Recording usage for user message - input_tokens: {input_tokens}")
                
                # Calculate PFT
                pft_info = token_conversion.calculate_pft(
                    input_tokens=input_tokens,
                    output_tokens=0,
                    storage_bytes=0
                )
                
                # Log the type for debugging
                logger.debug(f"PFT type before usage: {type(pft_info['total_pft'])}")
                
                usage_record = await usage_service.record_usage(
                    db=db,
                    user_id=user_id,
                    chat_id=chat_id,
                    message_id=user_message.id,
                    input_tokens=input_tokens,
                    output_tokens=0,
                    storage_bytes=0,
                )
                logger.info(f"Created usage record: {usage_record}")
            except Exception as e:
                logger.error(f"Error recording user message usage: {str(e)}")
                # Continue execution even if usage recording fails

            # Initialize assistant message
            assistant_message = Message(
                chat_id=chat_id,
                content="",
                role="assistant"
            )
            db.add(assistant_message)
            db.commit()
            db.refresh(assistant_message)
            message_id = assistant_message.id

            # Get conversation context
            messages = await self.get_chat_context(db, chat_id)
            
            # Prepare current message content
            current_message_content = []
            
            # Add file contents if any
            if files:
                for file in files:
                    try:
                        # Determine file type
                        media_type = "application/pdf" if file.original_name.lower().endswith('.pdf') else "text/plain"
                        file_content = await self.get_file_content(file.s3_key, media_type)
                        current_message_content.append(file_content)
                    except Exception as e:
                        logger.error(f"Error reading file content: {str(e)}")

            # Add text content
            current_message_content.append({
                "type": "text",
                "text": content
            })
            
            # Add current message to context
            messages.append({
                "role": "user",
                "content": current_message_content
            })

            accumulated_content = ""

            # Create the message stream with context
            with self.anthropic.messages.stream(
                model="claude-3-5-sonnet-latest",
                max_tokens=4096,
                messages=messages,
                system="You are a helpful AI assistant. When PDFs or documents are shared, analyze them thoroughly including any charts, tables, or visual elements."
            ) as stream:
                try:
                    for chunk in stream:
                        if hasattr(chunk, 'delta') and hasattr(chunk.delta, 'text'):
                            delta_text = chunk.delta.text
                            if delta_text:
                                accumulated_content += delta_text

                                # Update message in database
                                db.query(Message).filter(Message.id == message_id).update({
                                    "content": accumulated_content
                                })
                                db.commit()

                                # Send chunk to client
                                yield f"data: {json.dumps({'content': delta_text, 'message_id': message_id, 'done': False})}\n\n"

                    # Record assistant message usage
                    try:
                        output_tokens = len(accumulated_content.split())
                        logger.info(f"Recording usage for assistant message - output_tokens: {output_tokens}")
                        
                        # Calculate PFT
                        pft_info = token_conversion.calculate_pft(
                            input_tokens=0,
                            output_tokens=output_tokens,
                            storage_bytes=0
                        )
                        
                        # Log the type for debugging
                        logger.debug(f"PFT type before usage: {type(pft_info['total_pft'])}")
                        
                        usage_record = await usage_service.record_usage(
                            db=db,
                            user_id=user_id,
                            chat_id=chat_id,
                            message_id=message_id,
                            input_tokens=0,
                            output_tokens=output_tokens,
                            storage_bytes=0,
                        )
                        logger.info(f"Created assistant usage record: {usage_record}")
                    except Exception as e:
                        logger.error(f"Error recording assistant message usage: {str(e)}")

                except Exception as e:
                    logger.error(f"Error processing message chunk: {str(e)}")
                    yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"

            # Final update
            if accumulated_content:
                try:
                    db.query(Message).filter(Message.id == message_id).update({
                        "content": accumulated_content
                    })
                    db.commit()
                except Exception as e:
                    logger.error(f"Error in final update: {str(e)}")

            yield f"data: {json.dumps({'done': True})}\n\n"

        except Exception as e:
            logger.error(f"Error in send_message: {str(e)}")
            yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"

    async def get_user_chats(
        self, 
        db: Session, 
        user_id: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Chat]:
        return db.query(Chat).filter(
            Chat.user_id == user_id,
            Chat.deleted == False
        ).order_by(Chat.updated_at.desc()).offset(skip).limit(limit).all()

    async def get_chat_messages(
        self, 
        db: Session, 
        chat_id: int, 
        user_id: str
    ) -> List[Message]:
        chat = db.query(Chat).filter(
            Chat.id == chat_id,
            Chat.user_id == user_id,
            Chat.deleted == False
        ).first()
        
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
            
        return db.query(Message).filter(
            Message.chat_id == chat_id,
            Message.deleted == False
        ).order_by(Message.created_at.asc()).all()

    async def delete_chat(self, db: Session, chat_id: int, user_id: str):
        chat = db.query(Chat).filter(
            Chat.id == chat_id,
            Chat.user_id == user_id,
            Chat.deleted == False
        ).first()
        
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        
        chat.deleted = True
        chat.deleted_at = datetime.now()
        db.commit()

chat_service = ChatService()
