"""Chat service for integrated chat functionality."""

from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Conversation, Message
from ..repositories import UserRepository, ConversationRepository, MessageRepository
from ..schemas.chat import ChatRequest, ChatResponse, MessageInResponse
from .conversation import ConversationService
from .message import MessageService


class ChatService:
    """Service for integrated chat functionality."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repository = UserRepository(db)
        self.conversation_repository = ConversationRepository(db)
        self.message_repository = MessageRepository(db)
        self.conversation_service = ConversationService(db)
        self.message_service = MessageService(db)

    async def process_chat(self, chat_data: ChatRequest) -> ChatResponse:
        """Process a chat message and return AI response."""
        # Verify user exists
        user = await self.user_repository.get_by_id(chat_data.user_id)
        if not user:
            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Create or get conversation
        if chat_data.conversation_id is None:
            conversation = Conversation(user_id=chat_data.user_id)
            conversation = await self.conversation_repository.create(conversation)
            conversation_id = conversation.id
        else:
            conversation = await self.conversation_service.get_conversation_by_id(
                chat_data.conversation_id
            )
            conversation_id = conversation.id

        # Store user message
        user_message = Message(
            conversation_id=conversation_id, role="user", content=chat_data.message
        )
        user_message = await self.message_repository.create(user_message)

        # TODO: Integrate with AI agent here
        # For now, simple echo response
        ai_response_content = await self._generate_ai_response(chat_data.message)

        # Store AI response
        assistant_message = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=ai_response_content,
        )
        assistant_message = await self.message_repository.create(assistant_message)

        return ChatResponse(
            conversation_id=conversation_id,
            user_message=MessageInResponse(
                id=user_message.id, content=user_message.content
            ),
            assistant_message=MessageInResponse(
                id=assistant_message.id, content=assistant_message.content
            ),
        )

    async def _generate_ai_response(self, user_message: str) -> str:
        """Generate AI response. To be replaced with actual AI integration."""
        # TODO: Replace with actual AI agent call
        return f"Echo: {user_message}"

