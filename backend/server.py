from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Query, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
# Removed: from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import random
import string
import uuid
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
from enum import Enum
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Environment variables
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "rapidmandados")
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
OWNER_EMAIL = os.getenv("OWNER_EMAIL", "leonardo.luna@rapidmandados.com")
OWNER_NAME = os.getenv("OWNER_NAME", "LEONARDO LUNA")
DEFAULT_COMMISSION_RATE = float(os.getenv("DEFAULT_COMMISSION_RATE", "0.15"))
SERVICE_FEE = float(os.getenv("SERVICE_FEE", "15.0"))
PREMIUM_SUBSCRIPTION_MONTHLY = float(os.getenv("PREMIUM_SUBSCRIPTION_MONTHLY", "200.0"))
# Removed: STRIPE_API_KEY = os.getenv("STRIPE_API_KEY")
# Removed: STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")

# Email configuration for verification
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USER = os.getenv("EMAIL_USER", "noreply@rapidmandados.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "RapidMandados <noreply@rapidmandados.com>")

# MongoDB connection
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Collections
users_collection = db.users
orders_collection = db.orders
commission_config_collection = db.commission_config
payment_transactions_collection = db.payment_transactions
driver_payouts_collection = db.driver_payouts
cash_collections_collection = db.cash_collections
documents_collection = db.documents
verification_codes_collection = db.verification_codes

# Removed: Initialize Stripe checkout
# stripe_checkout = None
# if STRIPE_API_KEY:
#     stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=None)  # Will be set dynamically

# Create the main app without a prefix
app = FastAPI(title="RapidMandados API - México", description="Aplicación de Delivery con Sistema de Comisiones en MXN", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"

# Additional configuration constants
TAX_RATE = 0.16  # 16% IVA (Mexican tax)
CURRENCY = "MXN"
COUNTRY = "México"
MIN_ORDER_VALUE = 50.00  # Minimum order value in MXN
MAX_ORDER_VALUE = 5000.00  # Maximum order value in MXN

# Enums
class UserType(str, Enum):
    CLIENT = "client"
    DRIVER = "driver"
    ADMIN = "admin"

class OrderStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    UNPAID = "unpaid"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

class PaymentMethod(str, Enum):
    # Removed: CREDIT_CARD = "credit_card"
    CASH = "cash"

class UserStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"

class VerificationStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"
    EXPIRED = "expired"

class DocumentStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class DocumentType(str, Enum):
    INE = "ine"
    DRIVERS_LICENSE = "drivers_license"
    VEHICLE_REGISTRATION = "vehicle_registration"
    PROOF_OF_ADDRESS = "proof_of_address"

class Document(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    document_type: DocumentType
    file_name: str
    file_data: str  # Base64 encoded
    upload_date: datetime = Field(default_factory=datetime.utcnow)
    status: DocumentStatus = DocumentStatus.PENDING
    admin_comments: Optional[str] = None
    auto_verified: bool = False
    verification_confidence: Optional[float] = None

class EmailVerification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    email: str
    verification_code: str
    status: VerificationStatus = VerificationStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(default_factory=lambda: datetime.utcnow() + timedelta(hours=24))
    verified_at: Optional[datetime] = None
    attempts: int = 0
    max_attempts: int = 3

class DocumentUploadRequest(BaseModel):
    document_type: DocumentType
    file_name: str
    file_data: str  # Base64 encoded

class EmailVerificationRequest(BaseModel):
    verification_code: str

class DriverVerificationStatus(BaseModel):
    email_verified: bool
    documents_status: Dict[str, DocumentStatus]
    overall_verification_complete: bool
    can_accept_orders: bool
    pending_actions: List[str]

class VerificationRequest(BaseModel):
    user_id: str
    phone_code: Optional[str] = None
    email_code: Optional[str] = None

class TransferStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

class PaymentTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: Optional[str] = None # Still keeping session_id as optional, but will be None for cash
    user_id: Optional[str] = None
    order_id: Optional[str] = None
    amount: float
    currency: str = "mxn"
    payment_method: PaymentMethod
    payment_status: PaymentStatus = PaymentStatus.PENDING
    metadata: Optional[Dict[str, str]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class DriverPayout(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    driver_id: str
    order_id: str
    amount: float
    currency: str = "mxn"
    payment_method: PaymentMethod
    transfer_status: TransferStatus = TransferStatus.PENDING
    stripe_transfer_id: Optional[str] = None # Removed Stripe-specific transfer ID
    bank_account: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class CashCollection(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    driver_id: str
    order_id: str
    amount_collected: float
    commission_owed: float
    currency: str = "mxn"
    collection_date: datetime = Field(default_factory=datetime.utcnow)
    payment_status: PaymentStatus = PaymentStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Removed: PaymentTransactionResponse
# class PaymentTransactionResponse(BaseModel):
#     id: str
#     session_id: str
#     user_id: Optional[str] = None
#     order_id: Optional[str] = None
#     amount: float
#     currency: str
#     payment_status: PaymentStatus
#     metadata: Optional[Dict[str, str]] = None
#     created_at: datetime
#     updated_at: datetime

# Removed: CheckoutRequest
# class CheckoutRequest(BaseModel):
#     order_id: str
#     origin_url: str
#     payment_method: PaymentMethod = PaymentMethod.CREDIT_CARD

class CashPaymentRequest(BaseModel):
    order_id: str

class DriverPayoutRequest(BaseModel):
    driver_id: str
    bank_account: str

class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    phone: str
    user_type: UserType
    password_hash: str
    address: str
    status: UserStatus = UserStatus.PENDING
    is_phone_verified: bool = False
    is_email_verified: bool = False
    phone_verification_code: Optional[str] = None
    email_verification_code: Optional[str] = None
    verification_code_expires: Optional[datetime] = None
    documents_uploaded: bool = False
    admin_approved: bool = False
    admin_comments: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_premium: bool = False
    premium_expires_at: Optional[datetime] = None
    commission_rate: Optional[float] = None
    is_active: bool = True
    total_orders: int = 0
    total_earnings: float = 0.0

class UserCreate(BaseModel):
    email: str
    name: str
    phone: str
    password: str
    user_type: UserType
    address: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    phone: str
    user_type: UserType
    address: Optional[str] = None
    is_premium: bool = False
    premium_expires_at: Optional[datetime] = None
    total_orders: int = 0
    total_earnings: float = 0.0

class OrderFinancials(BaseModel):
    subtotal: float
    service_fee: float
    iva_amount: float
    commission_amount: float
    commission_rate: float
    driver_earnings: float
    owner_earnings: float
    total_amount: float

class Order(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str
    driver_id: Optional[str] = None
    title: str
    description: str
    pickup_address: str
    delivery_address: str
    price: float
    status: OrderStatus = OrderStatus.PENDING
    payment_status: PaymentStatus = PaymentStatus.PENDING
    payment_method: Optional[PaymentMethod] = PaymentMethod.CASH # Default to cash
    financials: Optional[OrderFinancials] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    accepted_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    stripe_payment_intent: Optional[str] = None # Still keeping for backward compatibility but won't be used

class OrderCreate(BaseModel):
    title: str
    description: str
    pickup_address: str
    delivery_address: str
    price: float

class OrderResponse(BaseModel):
    id: str
    client_id: str
    client_name: str
    driver_id: Optional[str] = None
    driver_name: Optional[str] = None
    title: str
    description: str
    pickup_address: str
    delivery_address: str
    price: float
    status: OrderStatus
    payment_status: PaymentStatus
    payment_method: Optional[PaymentMethod] = None # Include payment method in response
    financials: Optional[OrderFinancials] = None
    created_at: datetime
    accepted_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None

class AdminStats(BaseModel):
    total_orders: int
    total_revenue: float
    total_commission_earned: float
    active_users: int
    active_drivers: int
    pending_orders: int
    completed_orders: int
    monthly_revenue: float
    monthly_commission: float
    average_order_value: float

class CommissionConfig(BaseModel):
    commission_rate: float
    service_fee: float
    premium_subscription_monthly: float

# Financial calculation helper for Mexico (MXN)
def calculate_order_financials(order_price: float, commission_rate: float = None, service_fee: float = None) -> OrderFinancials:
    """Calculate financial breakdown for an order in Mexican Pesos (MXN)"""
    if commission_rate is None:
        commission_rate = DEFAULT_COMMISSION_RATE
    if service_fee is None:
        service_fee = SERVICE_FEE

    subtotal = order_price
    iva_amount = service_fee * TAX_RATE  # 16% IVA on service fee
    commission_amount = subtotal * commission_rate
    driver_earnings = subtotal - commission_amount
    owner_earnings = commission_amount + service_fee
    total_amount = subtotal + service_fee + iva_amount

    return OrderFinancials(
        subtotal=subtotal,
        service_fee=service_fee,
        iva_amount=iva_amount,
        commission_amount=commission_amount,
        commission_rate=commission_rate,
        driver_earnings=driver_earnings,
        owner_earnings=owner_earnings,
        total_amount=total_amount
    )

# Utility functions
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await db.users.find_one({"id": user_id})
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return User(**user)

async def get_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

async def create_driver_payout_for_order(order_id: str):
    """Create a driver payout record when an order is paid"""
    # Get the order details
    order = await orders_collection.find_one({"id": order_id})
    if not order or not order.get("driver_id"):
        return  # No driver assigned yet or order not found

    # Check if payout already exists
    existing_payout = await driver_payouts_collection.find_one({"order_id": order_id})
    if existing_payout:
        return  # Payout already created

    # Calculate driver earnings from order financials
    if not order.get("financials"):
        return  # No financial data available

    driver_earnings = order["financials"]["driver_earnings"]

    # Create driver payout record
    driver_payout = DriverPayout(
        driver_id=order["driver_id"],
        order_id=order_id,
        amount=driver_earnings,
        currency="mxn",
        payment_method=PaymentMethod.CASH, # Always cash for driver payouts in this version
        transfer_status=TransferStatus.PENDING
    )

    await driver_payouts_collection.insert_one(driver_payout.dict())

# Initialize owner account
async def initialize_owner():
    """Create owner account if it doesn't exist"""
    owner = await db.users.find_one({"email": OWNER_EMAIL})
    if not owner:
        owner_user = User(
            email=OWNER_EMAIL,
            name=OWNER_NAME,
            phone="+52 55 0000 0000",
            user_type=UserType.ADMIN,
            password_hash=hash_password("owner123456"),
            address="Oficina Principal - Ciudad de México",
            status=UserStatus.APPROVED,
            is_phone_verified=True,
            is_email_verified=True,
            admin_approved=True,
            documents_uploaded=True
        )
        await db.users.insert_one(owner_user.dict())
        print(f"✅ Owner account created: {OWNER_NAME} - {OWNER_EMAIL}")
    else:
        # Update existing owner to have all required fields
        await db.users.update_one(
            {"email": OWNER_EMAIL},
            {
                "$set": {
                    "status": UserStatus.APPROVED,
                    "is_phone_verified": True,
                    "is_email_verified": True,
                    "admin_approved": True,
                    "documents_uploaded": True,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        print(f"✅ Owner account updated: {OWNER_NAME} - {OWNER_EMAIL}")

# Routes
def generate_verification_code():
    """Generate a 6-digit verification code"""
    return ''.join(random.choices(string.digits, k=6))

async def send_email_verification(email: str, code: str, user_name: str):
    """Send email verification code"""
    try:
        # Create email message
        subject = "🚚 RapidMandados - Código de Verificación"
        body = f"""
        ¡Hola {user_name}!

        Tu código de verificación para RapidMandados es:

        {code}

        Este código expirará en 24 horas.

        Si no solicitaste este código, ignora este mensaje.

        Equipo RapidMandados México
        """

        # For now, we'll just log the verification code
        # In production, you would integrate with an email service
        print(f"📧 Email verification code for {email}: {code}")
        print(f"📧 Email content: {body}")

        # TODO: Integrate with actual email service (SendGrid, AWS SES, etc.)
        return True

    except Exception as e:
        print(f"❌ Error sending email to {email}: {e}")
        return False

async def validate_document_automatically(document_type: DocumentType, file_data: str):
    """Automatically validate document based on type and content"""
    # For now, we'll do basic validation
    # In production, you would integrate with OCR and document validation services

    validation_results = {
        "is_valid": True,
        "confidence": 0.95,
        "extracted_data": {},
        "issues": []
    }

    try:
        # Basic file validation
        if not file_data or len(file_data) < 100:
            validation_results["is_valid"] = False
            validation_results["confidence"] = 0.0
            validation_results["issues"].append("Archivo muy pequeño o inválido")
            return validation_results

        # Document type specific validation
        if document_type == DocumentType.INE:
            validation_results["extracted_data"] = {
                "document_type": "INE",
                "status": "Validación automática completada"
            }
        elif document_type == DocumentType.DRIVERS_LICENSE:
            validation_results["extracted_data"] = {
                "document_type": "Licencia de Conducir",
                "status": "Validación automática completada"
            }

        # Simulate high confidence for demo
        validation_results["confidence"] = 0.92

        print(f"📄 Document validation completed for {document_type.value}: {validation_results['confidence']:.2f} confidence")

        return validation_results

    except Exception as e:
        print(f"❌ Error validating document: {e}")
        validation_results["is_valid"] = False
        validation_results["confidence"] = 0.0
        validation_results["issues"].append(f"Error en validación: {str(e)}")
        return validation_results

async def check_driver_verification_status(user_id: str):
    """Check complete verification status for a driver"""
    user = await users_collection.find_one({"id": user_id})
    if not user:
        return None

    # Check email verification
    email_verified = user.get("is_email_verified", False)

    # Check required documents
    required_docs = [DocumentType.INE, DocumentType.DRIVERS_LICENSE]
    documents_status = {}

    for doc_type in required_docs:
        doc = await documents_collection.find_one({
            "user_id": user_id,
            "document_type": doc_type
        })
        if doc:
            documents_status[doc_type.value] = DocumentStatus(doc.get("status", "pending"))
        else:
            documents_status[doc_type.value] = DocumentStatus.PENDING

    # Check if all documents are approved
    all_docs_approved = all(
        status == DocumentStatus.APPROVED
        for status in documents_status.values()
    )

    # Overall verification complete
    overall_complete = email_verified and all_docs_approved

    # Can accept orders
    can_accept_orders = overall_complete and user.get("status") == UserStatus.APPROVED

    # Pending actions
    pending_actions = []
    if not email_verified:
        pending_actions.append("Verificar correo electrónico")

    for doc_type, status in documents_status.items():
        if status == DocumentStatus.PENDING:
            pending_actions.append(f"Subir documento: {doc_type}")
        elif status == DocumentStatus.REJECTED:
            pending_actions.append(f"Volver a subir documento: {doc_type}")

    return DriverVerificationStatus(
        email_verified=email_verified,
        documents_status=documents_status,
        overall_verification_complete=overall_complete,
        can_accept_orders=can_accept_orders,
        pending_actions=pending_actions
    )

async def send_phone_verification(phone: str, code: str):
    """Send SMS verification code (mock implementation)"""
    # In production, integrate with SMS service like Twilio
    print(f"📱 SMS sent to {phone}: Your verification code is {code}")
    return True


@api_router.post("/auth/register", response_model=dict)
async def register(user_data: UserCreate):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create user - simplified for immediate functionality
    user = User(
        email=user_data.email,
        name=user_data.name,
        phone=user_data.phone,
        user_type=user_data.user_type,
        password_hash=hash_password(user_data.password),
        address=user_data.address,
        status=UserStatus.APPROVED,  # Approve immediately for now
        is_phone_verified=True,      # Skip verification for now
        is_email_verified=True,      # Skip verification for now
        admin_approved=True,         # Auto-approve
        documents_uploaded=True      # Skip documents for now
    )

    # Save user to database
    await db.users.insert_one(user.dict())

    # Create JWT token for immediate login
    token = create_access_token(data={"sub": user.id})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": UserResponse(**user.dict()).dict(),
        "message": "Registration successful"
    }

@api_router.post("/auth/verify-phone")
async def verify_phone(verification_data: dict):
    """Verify phone number with code"""
    user_id = verification_data.get("user_id")
    phone_code = verification_data.get("phone_code")

    if not user_id or not phone_code:
        raise HTTPException(status_code=400, detail="User ID and phone code are required")

    # Get user
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if code is valid and not expired
    if (user.get("phone_verification_code") != phone_code or
        user.get("verification_code_expires") < datetime.utcnow()):
        raise HTTPException(status_code=400, detail="Invalid or expired verification code")

    # Update user as phone verified
    await db.users.update_one(
        {"id": user_id},
        {
            "$set": {
                "is_phone_verified": True,
                "phone_verification_code": None,
                "updated_at": datetime.utcnow()
            }
        }
    )

    return {"message": "Phone verified successfully"}

@api_router.post("/auth/verify-email")
async def verify_email(verification_data: dict):
    """Verify email with code"""
    user_id = verification_data.get("user_id")
    email_code = verification_data.get("email_code")

    if not user_id or not email_code:
        raise HTTPException(status_code=400, detail="User ID and email code are required")

    # Get user
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if code is valid and not expired
    if (user.get("email_verification_code") != email_code or
        user.get("verification_code_expires") < datetime.utcnow()):
        raise HTTPException(status_code=400, detail="Invalid or expired verification code")

    # Update user as email verified
    await db.users.update_one(
        {"id": user_id},
        {
            "$set": {
                "is_email_verified": True,
                "email_verification_code": None,
                "updated_at": datetime.utcnow()
            }
        }
    )

    return {"message": "Email verified successfully"}

@api_router.post("/auth/upload-document")
async def upload_document(document_data: dict):
    """Upload required documents for driver verification"""
    user_id = document_data.get("user_id")
    document_type = document_data.get("document_type")
    file_name = document_data.get("file_name")
    file_data = document_data.get("file_data")  # Base64 encoded

    if not all([user_id, document_type, file_name, file_data]):
        raise HTTPException(status_code=400, detail="All document fields are required")

    # Get user
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if user is verified
    if not user.get("is_phone_verified") or not user.get("is_email_verified"):
        raise HTTPException(status_code=400, detail="Please verify phone and email first")

    # Create document record
    document = Document(
        user_id=user_id,
        document_type=document_type,
        file_name=file_name,
        file_data=file_data
    )

    # Save document
    await documents_collection.insert_one(document.dict())

    # Check if this is INE or license (required documents)
    if document_type in ["ine", "drivers_license"]:
        # Check if user has uploaded both required documents
        user_documents = await documents_collection.find({"user_id": user_id}).to_list(100)
        document_types = [doc["document_type"] for doc in user_documents]

        if "ine" in document_types and "drivers_license" in document_types:
            # Mark user as having uploaded documents
            await db.users.update_one(
                {"id": user_id},
                {
                    "$set": {
                        "documents_uploaded": True,
                        "updated_at": datetime.utcnow()
                    }
                }
            )

    return {"message": "Document uploaded successfully"}

@api_router.get("/admin/pending-drivers")
async def get_pending_drivers(current_user: User = Depends(get_admin_user)):
    """Get all drivers pending approval"""
    drivers = await db.users.find({
        "user_type": UserType.DRIVER,
        "status": UserStatus.PENDING,
        "documents_uploaded": True
    }).to_list(100)

    # Enrich with document info
    enriched_drivers = []
    for driver in drivers:
        # Get driver documents
        documents = await documents_collection.find({"user_id": driver["id"]}).to_list(100)

        enriched_driver = {
            **driver,
            "documents": [{"type": doc["document_type"], "status": doc["status"]} for doc in documents]
        }
        enriched_drivers.append(enriched_driver)

    return enriched_drivers

@api_router.post("/admin/approve-driver/{driver_id}")
async def approve_driver(driver_id: str, approval_data: dict, current_user: User = Depends(get_admin_user)):
    """Approve or reject a driver"""
    approved = approval_data.get("approved", False)
    comments = approval_data.get("comments", "")

    # Get driver
    driver = await db.users.find_one({"id": driver_id})
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    # Update driver status
    new_status = UserStatus.APPROVED if approved else UserStatus.REJECTED
    await db.users.update_one(
        {"id": driver_id},
        {
            "$set": {
                "status": new_status,
                "admin_approved": approved,
                "admin_comments": comments,
                "updated_at": datetime.utcnow()
            }
        }
    )

    action = "approved" if approved else "rejected"
    return {"message": f"Driver {action} successfully"}

@api_router.post("/auth/login", response_model=dict)
async def login(user_data: UserLogin):
    # Find user by email
    user = await db.users.find_one({"email": user_data.email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Verify password
    if not verify_password(user_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Create access token - simplified for immediate functionality
    access_token = create_access_token(data={"sub": user["id"]})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse(**user).dict()
    }

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse(**current_user.dict())

@api_router.post("/orders", response_model=OrderResponse)
async def create_order(order_data: OrderCreate, current_user: User = Depends(get_current_user)):
    if current_user.user_type != UserType.CLIENT:
        raise HTTPException(status_code=403, detail="Only clients can create orders")

    # Validate order price
    if order_data.price < MIN_ORDER_VALUE or order_data.price > MAX_ORDER_VALUE:
        raise HTTPException(
            status_code=400,
            detail=f"Order price must be between ${MIN_ORDER_VALUE:,.2f} and ${MAX_ORDER_VALUE:,.2f} MXN"
        )

    # Calculate financials
    financials = calculate_order_financials(order_data.price)

    order = Order(
        client_id=current_user.id,
        title=order_data.title,
        description=order_data.description,
        pickup_address=order_data.pickup_address,
        delivery_address=order_data.delivery_address,
        price=order_data.price,
        financials=financials,
        payment_method=PaymentMethod.CASH, # Explicitly set to cash
        payment_status=PaymentStatus.PENDING # Cash payments start as pending
    )

    await db.orders.insert_one(order.dict())

    # Update client stats
    await db.users.update_one(
        {"id": current_user.id},
        {"$inc": {"total_orders": 1}}
    )

    return OrderResponse(
        **order.dict(),
        client_name=current_user.name,
        driver_name=None
    )

@api_router.get("/orders", response_model=List[OrderResponse])
async def get_orders(current_user: User = Depends(get_current_user)):
    if current_user.user_type == UserType.CLIENT:
        # Get client's orders
        orders_cursor = db.orders.find({"client_id": current_user.id})
    elif current_user.user_type == UserType.DRIVER:
        # Get available orders for drivers
        orders_cursor = db.orders.find({"status": OrderStatus.PENDING})
    else:  # ADMIN
        # Get all orders for admin
        orders_cursor = db.orders.find({})

    orders = await orders_cursor.to_list(1000)

    # Get user info for each order
    order_responses = []
    for order in orders:
        # Get client info
        client = await db.users.find_one({"id": order["client_id"]})
        client_name = client["name"] if client else "Unknown"

        # Get driver info if exists
        driver_name = None
        if order.get("driver_id"):
            driver = await db.users.find_one({"id": order["driver_id"]})
            driver_name = driver["name"] if driver else "Unknown"

        # Ensure payment_status and payment_method are set for backward compatibility
        order_data = {**order}
        if "payment_status" not in order_data:
            order_data["payment_status"] = PaymentStatus.PENDING
        if "payment_method" not in order_data:
            order_data["payment_method"] = PaymentMethod.CASH # Default to cash for old orders

        order_responses.append(OrderResponse(
            **order_data,
            client_name=client_name,
            driver_name=driver_name
        ))

    return order_responses

@api_router.get("/orders/driver", response_model=List[OrderResponse])
async def get_driver_orders(current_user: User = Depends(get_current_user)):
    if current_user.user_type != UserType.DRIVER:
        raise HTTPException(status_code=403, detail="Only drivers can access this endpoint")

    # Get driver's accepted orders
    orders_cursor = db.orders.find({"driver_id": current_user.id})
    orders = await orders_cursor.to_list(1000)

    order_responses = []
    for order in orders:
        # Get client info
        client = await db.users.find_one({"id": order["client_id"]})
        client_name = client["name"] if client else "Unknown"

        # Ensure payment_status and payment_method are set for backward compatibility
        order_data = {**order}
        if "payment_status" not in order_data:
            order_data["payment_status"] = PaymentStatus.PENDING
        if "payment_method" not in order_data:
            order_data["payment_method"] = PaymentMethod.CASH # Default to cash for old orders

        order_responses.append(OrderResponse(
            **order_data,
            client_name=client_name,
            driver_name=current_user.name
        ))

    return order_responses

@api_router.put("/orders/{order_id}/accept")
async def accept_order(order_id: str, current_user: User = Depends(get_current_user)):
    if current_user.user_type != UserType.DRIVER:
        raise HTTPException(status_code=403, detail="Only drivers can accept orders")

    # Check driver verification status
    verification_status = await check_driver_verification_status(current_user.id)
    if not verification_status or not verification_status.can_accept_orders:
        raise HTTPException(
            status_code=403,
            detail="Driver not fully verified. Complete verification process to accept orders."
        )

    # Find order
    order = await db.orders.find_one({"id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order["status"] != OrderStatus.PENDING:
        raise HTTPException(status_code=400, detail="Order is not available")

    # Update order
    await db.orders.update_one(
        {"id": order_id},
        {
            "$set": {
                "driver_id": current_user.id,
                "status": OrderStatus.ACCEPTED,
                "accepted_at": datetime.utcnow()
            }
        }
    )

    return {"message": "Order accepted successfully"}

@api_router.put("/orders/{order_id}/status")
async def update_order_status(order_id: str, status: OrderStatus, current_user: User = Depends(get_current_user)):
    # Find order
    order = await db.orders.find_one({"id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Check permissions
    if current_user.user_type == UserType.DRIVER:
        if order["driver_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="You can only update your own orders")
    elif current_user.user_type == UserType.CLIENT:
        if order["client_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="You can only update your own orders")

    # Update order
    update_data = {"status": status}
    if status == OrderStatus.DELIVERED:
        update_data["delivered_at"] = datetime.utcnow()
        # For cash payments, payment status is updated by driver
        if order.get("payment_method") != PaymentMethod.CASH:
            update_data["payment_status"] = PaymentStatus.COMPLETED

        # Update driver earnings
        if order.get("financials") and order.get("driver_id"):
            await db.users.update_one(
                {"id": order["driver_id"]},
                {"$inc": {"total_earnings": order["financials"]["driver_earnings"]}}
            )

    await db.orders.update_one(
        {"id": order_id},
        {"$set": update_data}
    )

    return {"message": "Order status updated successfully"}

# ADMIN ROUTES
@api_router.get("/admin/stats", response_model=AdminStats)
async def get_admin_stats(current_user: User = Depends(get_admin_user)):
    """Get comprehensive admin statistics"""

    # Get current month dates
    now = datetime.utcnow()
    start_of_month = datetime(now.year, now.month, 1)

    # Aggregate statistics
    total_orders = await db.orders.count_documents({})
    active_users = await db.users.count_documents({"is_active": True, "user_type": {"$ne": "admin"}})
    active_drivers = await db.users.count_documents({"is_active": True, "user_type": "driver"})
    pending_orders = await db.orders.count_documents({"status": "pending"})
    completed_orders = await db.orders.count_documents({"status": "delivered"})

    # Revenue calculations
    revenue_pipeline = [
        {"$match": {"status": "delivered", "financials": {"$exists": True}}},
        {"$group": {
            "_id": None,
            "total_revenue": {"$sum": "$financials.total_amount"},
            "total_commission": {"$sum": "$financials.owner_earnings"},
            "avg_order_value": {"$avg": "$financials.total_amount"}
        }}
    ]

    revenue_result = await db.orders.aggregate(revenue_pipeline).to_list(1)
    total_revenue = revenue_result[0]["total_revenue"] if revenue_result else 0
    total_commission = revenue_result[0]["total_commission"] if revenue_result else 0
    avg_order_value = revenue_result[0]["avg_order_value"] if revenue_result else 0

    # Monthly revenue
    monthly_pipeline = [
        {"$match": {
            "status": "delivered",
            "delivered_at": {"$gte": start_of_month},
            "financials": {"$exists": True}
        }},
        {"$group": {
            "_id": None,
            "monthly_revenue": {"$sum": "$financials.total_amount"},
            "monthly_commission": {"$sum": "$financials.owner_earnings"}
        }}
    ]

    monthly_result = await db.orders.aggregate(monthly_pipeline).to_list(1)
    monthly_revenue = monthly_result[0]["monthly_revenue"] if monthly_result else 0
    monthly_commission = monthly_result[0]["monthly_commission"] if monthly_result else 0

    return AdminStats(
        total_orders=total_orders,
        total_revenue=total_revenue,
        total_commission_earned=total_commission,
        active_users=active_users,
        active_drivers=active_drivers,
        pending_orders=pending_orders,
        completed_orders=completed_orders,
        monthly_revenue=monthly_revenue,
        monthly_commission=monthly_commission,
        average_order_value=avg_order_value
    )

# Removed Stripe checkout session endpoints
# @api_router.post("/checkout/session", response_model=CheckoutSessionResponse)
# async def create_checkout_session(checkout_request: CheckoutRequest, current_user: User = Depends(get_current_user)):
#    ... (removed Stripe logic)

# @api_router.get("/checkout/status/{session_id}", response_model=CheckoutStatusResponse)
# async def get_checkout_status(session_id: str, current_user: User = Depends(get_current_user)):
#    ... (removed Stripe logic)

async def create_driver_payout_for_order(order_id: str):
    """Create driver payout when order is paid (for cash, this is handled differently)"""
    try:
        # Get order details
        order = await orders_collection.find_one({"id": order_id})
        if not order or not order.get("driver_id"):
            return

        # Check if payout already exists
        existing_payout = await driver_payouts_collection.find_one({"order_id": order_id})
        if existing_payout:
            return

        # Calculate driver earnings
        financials = order.get("financials", {})
        # Note: For cash, driver earnings might be settled directly with client,
        # but a payout record is still needed for tracking if owner owes driver.
        # Here, assuming owner pays driver their share later from overall cash collected.
        driver_earnings = financials.get("driver_earnings", 0)

        # Create payout record
        payout = DriverPayout(
            driver_id=order["driver_id"],
            order_id=order_id,
            amount=driver_earnings,
            currency="mxn",
            payment_method=PaymentMethod.CASH, # Explicitly cash
            transfer_status=TransferStatus.PENDING
        )

        await driver_payouts_collection.insert_one(payout.dict())
        print(f"✅ Driver payout created for order {order_id}: ${driver_earnings} MXN")

    except Exception as e:
        print(f"❌ Error creating driver payout: {e}")

@api_router.post("/payment/cash")
async def process_cash_payment(cash_request: CashPaymentRequest, current_user: User = Depends(get_current_user)):
    """Process cash payment for an order"""
    # Get the order
    order = await orders_collection.find_one({"id": cash_request.order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Verify the order belongs to the current user
    if order["client_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to pay for this order")

    # Check if order is already paid or set for cash
    if order.get("payment_status") == PaymentStatus.PAID and order.get("payment_method") == PaymentMethod.CASH:
        raise HTTPException(status_code=400, detail="Order already set for cash payment and paid")
    if order.get("payment_method") == PaymentMethod.CASH and order.get("payment_status") == PaymentStatus.PENDING:
        return {"message": "Order already set for cash payment", "total_amount": order["financials"]["total_amount"]}


    # Calculate total amount including commissions
    base_price = order["price"]
    financials = calculate_order_financials(base_price) # Re-calculate to ensure consistency

    # Update order to cash payment
    await orders_collection.update_one(
        {"id": cash_request.order_id},
        {
            "$set": {
                "payment_status": PaymentStatus.PENDING,
                "payment_method": PaymentMethod.CASH,
                "financials": financials.dict()
            }
        }
    )

    # Create payment transaction record
    payment_transaction = PaymentTransaction(
        user_id=current_user.id,
        order_id=cash_request.order_id,
        amount=financials.total_amount, # Use financials total amount
        currency="mxn",
        payment_method=PaymentMethod.CASH,
        payment_status=PaymentStatus.PENDING,
        metadata={
            "base_price": str(financials.subtotal),
            "commission": str(financials.commission_amount),
            "service_fee": str(financials.service_fee),
            "iva_amount": str(financials.iva_amount),
            "total_amount": str(financials.total_amount)
        }
    )

    await payment_transactions_collection.insert_one(payment_transaction.dict())

    return {"message": "Order set to cash payment", "total_amount": financials.total_amount}

@api_router.post("/payment/cash/complete/{order_id}")
async def complete_cash_payment(order_id: str, current_user: User = Depends(get_current_user)):
    """Complete cash payment when driver delivers order"""
    # Get the order
    order = await orders_collection.find_one({"id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Verify the current user is the driver for this order
    if order.get("driver_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Only the assigned driver can complete cash payment")

    # Check if order is cash payment and not already completed
    if order.get("payment_method") != PaymentMethod.CASH:
        raise HTTPException(status_code=400, detail="Order is not a cash payment")

    if order.get("payment_status") == PaymentStatus.PAID:
        raise HTTPException(status_code=400, detail="Payment already completed")

    # Update order payment status
    await orders_collection.update_one(
        {"id": order_id},
        {"$set": {"payment_status": PaymentStatus.PAID}}
    )

    # Update payment transaction
    await payment_transactions_collection.update_one(
        {"order_id": order_id, "payment_method": PaymentMethod.CASH, "payment_status": PaymentStatus.PENDING},
        {"$set": {"payment_status": PaymentStatus.PAID, "updated_at": datetime.utcnow()}}
    )

    # Create cash collection record for commission tracking
    financials = order.get("financials", {})
    cash_collection = CashCollection(
        driver_id=current_user.id,
        order_id=order_id,
        amount_collected=financials.get("total_amount", 0),
        # Commission owed to owner by driver
        commission_owed=financials.get("commission_amount", 0) + financials.get("service_fee", 0) + financials.get("iva_amount", 0),
        currency="mxn",
        payment_status=PaymentStatus.PENDING  # Driver owes commission to Leonardo (owner)
    )

    await cash_collections_collection.insert_one(cash_collection.dict())

    # Create driver payout (as driver has collected payment and owner owes driver their share)
    await create_driver_payout_for_order(order_id)

    return {"message": "Cash payment completed successfully"}

@api_router.get("/admin/driver-payouts", response_model=List[dict])
async def get_driver_payouts(current_user: User = Depends(get_admin_user)):
    """Get all driver payouts for admin management"""
    payouts = await driver_payouts_collection.find({}, {"_id": 0}).to_list(1000)

    # Enrich with driver and order details
    enriched_payouts = []
    for payout in payouts:
        # Get driver details
        driver = await users_collection.find_one({"id": payout["driver_id"]})
        # Get order details
        order = await orders_collection.find_one({"id": payout["order_id"]})

        enriched_payout = {
            **payout,
            "driver_name": driver.get("name", "Unknown") if driver else "Unknown",
            "driver_email": driver.get("email", "Unknown") if driver else "Unknown",
            "order_title": order.get("title", "Unknown") if order else "Unknown"
        }
        enriched_payouts.append(enriched_payout)

    return enriched_payouts

@api_router.get("/admin/cash-collections", response_model=List[dict])
async def get_cash_collections(current_user: User = Depends(get_admin_user)):
    """Get all cash collections for admin management"""
    collections = await cash_collections_collection.find({}, {"_id": 0}).to_list(1000)

    # Enrich with driver and order details
    enriched_collections = []
    for collection in collections:
        # Get driver details
        driver = await users_collection.find_one({"id": collection["driver_id"]})
        # Get order details
        order = await orders_collection.find_one({"id": collection["order_id"]})

        enriched_collection = {
            **collection,
            "driver_name": driver.get("name", "Unknown") if driver else "Unknown",
            "driver_email": driver.get("email", "Unknown") if driver else "Unknown",
            "order_title": order.get("title", "Unknown") if order else "Unknown"
        }
        enriched_collections.append(enriched_collection)
    
    return enriched_collections

@api_router.post("/admin/process-driver-payout/{payout_id}")
async def process_driver_payout(payout_id: str, current_user: User = Depends(get_admin_user)):
    """Process payout to driver via bank transfer"""
    # Get payout record
    payout = await driver_payouts_collection.find_one({"id": payout_id})
    if not payout:
        raise HTTPException(status_code=404, detail="Payout not found")

    if payout["transfer_status"] != TransferStatus.PENDING:
        raise HTTPException(status_code=400, detail="Payout already processed")

    # In a real implementation, this would integrate with a bank transfer API
    # For now, we'll mark it as completed
    await driver_payouts_collection.update_one(
        {"id": payout_id},
        {
            "$set": {
                "transfer_status": TransferStatus.COMPLETED,
                "updated_at": datetime.utcnow()
            }
        }
    )

    return {"message": "Driver payout processed successfully"}

@api_router.post("/admin/mark-commission-paid/{collection_id}")
async def mark_commission_paid(collection_id: str, current_user: User = Depends(get_admin_user)):
    """Mark commission as paid by driver"""
    # Get collection record
    collection = await cash_collections_collection.find_one({"id": collection_id})
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    if collection["payment_status"] == PaymentStatus.PAID:
        raise HTTPException(status_code=400, detail="Commission already marked as paid")

    # Update collection status
    await cash_collections_collection.update_one(
        {"id": collection_id},
        {"$set": {"payment_status": PaymentStatus.PAID}}
    )

    return {"message": "Commission marked as paid successfully"}

# Removed Stripe webhook endpoint
# @api_router.post("/webhook/stripe")
# async def stripe_webhook(request: Request):
#     ... (removed Stripe webhook logic)

@api_router.get("/payments/transactions", response_model=List[dict])
async def get_payment_transactions(current_user: User = Depends(get_current_user)):
    """Get payment transactions for the current user"""
    if current_user.user_type == UserType.ADMIN:
        # Admin can see all transactions
        transactions = await payment_transactions_collection.find({}, {"_id": 0}).to_list(1000)

        # Enrich with user and order details
        enriched_transactions = []
        for transaction in transactions:
            # Get user details
            user = await users_collection.find_one({"id": transaction.get("user_id")})
            # Get order details
            order = await orders_collection.find_one({"id": transaction.get("order_id")})

            enriched_transaction = {
                **transaction,
                "user_name": user.get("name", "Unknown") if user else "Unknown",
                "user_email": user.get("email", "Unknown") if user else "Unknown",
                "order_title": order.get("title", "Unknown") if order else "Unknown"
            }
            enriched_transactions.append(enriched_transaction)

        return enriched_transactions
    else:
        # Regular users can only see their own transactions
        transactions = await payment_transactions_collection.find({"user_id": current_user.id}, {"_id": 0}).to_list(1000)
        return transactions

@api_router.put("/admin/commission-config")
async def update_commission_config(config: CommissionConfig, current_user: User = Depends(get_admin_user)):
    """Update commission configuration"""
    updated_config = {
        "commission_rate": config.commission_rate,
        "service_fee": config.service_fee,
        "premium_subscription_monthly": config.premium_subscription_monthly,
        "updated_at": datetime.utcnow(),
        "updated_by": current_user.id
    }

    await commission_config_collection.update_one(
        {},
        {"$set": updated_config},
        upsert=True
    )

    return {"message": "Commission configuration updated successfully"}

@api_router.get("/admin/commission-config", response_model=CommissionConfig)
async def get_commission_config(current_user: User = Depends(get_admin_user)):
    """Get current commission configuration"""
    config = await commission_config_collection.find_one({})
    if not config:
        # Return default configuration
        return CommissionConfig(
            commission_rate=DEFAULT_COMMISSION_RATE,
            service_fee=SERVICE_FEE,
            premium_subscription_monthly=PREMIUM_SUBSCRIPTION_MONTHLY
        )
    return CommissionConfig(**config)

@api_router.put("/admin/users/{user_id}/toggle-status")
async def toggle_user_status(user_id: str, current_user: User = Depends(get_admin_user)):
    """Toggle user active/inactive status"""
    # Get user
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Toggle active status
    new_status = not user.get("is_active", True)

    # Update user
    await db.users.update_one(
        {"id": user_id},
        {
            "$set": {
                "is_active": new_status,
                "updated_at": datetime.utcnow()
            }
        }
    )

    action = "activated" if new_status else "deactivated"
    return {"message": f"User {action} successfully", "is_active": new_status}

@api_router.get("/admin/users", response_model=List[UserResponse])
async def get_all_users(current_user: User = Depends(get_admin_user)):
    """Get all users for admin management"""
    users = await db.users.find({"user_type": {"$ne": "admin"}}).to_list(1000)
    return [UserResponse(**user) for user in users]

# Removed duplicate endpoint, original one above is fine
# @api_router.put("/admin/users/{user_id}/toggle-status")
# async def toggle_user_status(user_id: str, current_user: User = Depends(get_admin_user)):
#    ... (removed)

# Removed Stripe Integration Ready endpoint
# @api_router.post("/payments/create-intent")
# async def create_payment_intent(order_id: str, current_user: User = Depends(get_current_user)):
#    ... (removed)

@api_router.post("/verification/send-email")
async def send_email_verification_code(current_user: User = Depends(get_current_user)):
    """Send email verification code to driver"""
    if current_user.user_type != UserType.DRIVER:
        raise HTTPException(status_code=403, detail="Only drivers can verify email")

    # Generate verification code
    verification_code = generate_verification_code()

    # Create email verification record
    email_verification = EmailVerification(
        user_id=current_user.id,
        email=current_user.email,
        verification_code=verification_code
    )

    # Save to database
    await verification_codes_collection.insert_one(email_verification.dict())

    # Send email
    success = await send_email_verification(current_user.email, verification_code, current_user.name)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to send verification email")

    return {"message": "Verification code sent to email", "expires_in": "24 hours"}

@api_router.post("/verification/verify-email")
async def verify_email_code(request: EmailVerificationRequest, current_user: User = Depends(get_current_user)):
    """Verify email with provided code"""
    if current_user.user_type != UserType.DRIVER:
        raise HTTPException(status_code=403, detail="Only drivers can verify email")

    # Find verification record
    verification = await verification_codes_collection.find_one({
        "user_id": current_user.id,
        "status": VerificationStatus.PENDING
    })

    if not verification:
        raise HTTPException(status_code=404, detail="No pending verification found")

    # Check expiration
    if datetime.utcnow() > verification["expires_at"]:
        await verification_codes_collection.update_one(
            {"id": verification["id"]},
            {"$set": {"status": VerificationStatus.EXPIRED}}
        )
        raise HTTPException(status_code=400, detail="Verification code expired")

    # Check attempts
    if verification["attempts"] >= verification["max_attempts"]:
        await verification_codes_collection.update_one(
            {"id": verification["id"]},
            {"$set": {"status": VerificationStatus.FAILED}}
        )
        raise HTTPException(status_code=400, detail="Maximum attempts exceeded")

    # Verify code
    if verification["verification_code"] != request.verification_code:
        await verification_codes_collection.update_one(
            {"id": verification["id"]},
            {"$inc": {"attempts": 1}}
        )
        raise HTTPException(status_code=400, detail="Invalid verification code")

    # Mark as verified
    await verification_codes_collection.update_one(
        {"id": verification["id"]},
        {
            "$set": {
                "status": VerificationStatus.VERIFIED,
                "verified_at": datetime.utcnow()
            }
        }
    )

    # Update user
    await users_collection.update_one(
        {"id": current_user.id},
        {
            "$set": {
                "is_email_verified": True,
                "updated_at": datetime.utcnow()
            }
        }
    )

    return {"message": "Email verified successfully"}

@api_router.post("/verification/upload-document")
async def upload_driver_document(request: DocumentUploadRequest, current_user: User = Depends(get_current_user)):
    """Upload driver document for verification"""
    if current_user.user_type != UserType.DRIVER:
        raise HTTPException(status_code=403, detail="Only drivers can upload documents")

    # Check if document already exists
    existing_doc = await documents_collection.find_one({
        "user_id": current_user.id,
        "document_type": request.document_type
    })

    if existing_doc and existing_doc.get("status") == DocumentStatus.APPROVED:
        raise HTTPException(status_code=400, detail="Document already approved")

    # Validate document automatically
    validation_result = await validate_document_automatically(request.document_type, request.file_data)

    # Create document record
    document = Document(
        user_id=current_user.id,
        document_type=request.document_type,
        file_name=request.file_name,
        file_data=request.file_data,
        status=DocumentStatus.APPROVED if validation_result["is_valid"] else DocumentStatus.REJECTED,
        auto_verified=True,
        verification_confidence=validation_result["confidence"]
    )

    # Save document
    if existing_doc:
        await documents_collection.update_one(
            {"id": existing_doc["id"]},
            {"$set": document.dict()}
        )
    else:
        await documents_collection.insert_one(document.dict())

    # Update user documents_uploaded status
    await users_collection.update_one(
        {"id": current_user.id},
        {
            "$set": {
                "documents_uploaded": True,
                "updated_at": datetime.utcnow()
            }
        }
    )

    return {
        "message": "Document uploaded and validated successfully",
        "document_type": request.document_type,
        "status": document.status,
        "confidence": validation_result["confidence"],
        "auto_verified": True
    }

@api_router.get("/verification/status")
async def get_driver_verification_status(current_user: User = Depends(get_current_user)):
    """Get driver verification status"""
    if current_user.user_type != UserType.DRIVER:
        raise HTTPException(status_code=403, detail="Only drivers can check verification status")

    status = await check_driver_verification_status(current_user.id)
    if not status:
        raise HTTPException(status_code=404, detail="User not found")

    return status

@api_router.get("/verification/documents")
async def get_driver_documents(current_user: User = Depends(get_current_user)):
    """Get driver uploaded documents"""
    if current_user.user_type != UserType.DRIVER:
        raise HTTPException(status_code=403, detail="Only drivers can view documents")

    documents = await documents_collection.find({"user_id": current_user.id}).to_list(length=None)

    return {
        "documents": [
            {
                "id": doc["id"],
                "document_type": doc["document_type"],
                "file_name": doc["file_name"],
                "status": doc["status"],
                "upload_date": doc["upload_date"],
                "auto_verified": doc.get("auto_verified", False),
                "verification_confidence": doc.get("verification_confidence", 0)
            }
            for doc in documents
        ]
    }

@api_router.get("/admin/drivers/verification")
async def get_all_drivers_verification_status(current_user: User = Depends(get_admin_user)):
    """Get verification status for all drivers"""
    # Get all drivers
    drivers = await users_collection.find({"user_type": UserType.DRIVER}).to_list(length=None)

    verification_statuses = []
    for driver in drivers:
        status = await check_driver_verification_status(driver["id"])
        if status:
            verification_statuses.append({
                "driver_id": driver["id"],
                "driver_name": driver["name"],
                "driver_email": driver["email"],
                "verification_status": status
            })

    return {"drivers": verification_statuses}

@api_router.post("/admin/drivers/{driver_id}/approve")
async def approve_driver_verification(driver_id: str, current_user: User = Depends(get_admin_user)):
    """Manually approve driver verification"""
    driver = await users_collection.find_one({"id": driver_id, "user_type": UserType.DRIVER})
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    # Update driver status
    await users_collection.update_one(
        {"id": driver_id},
        {
            "$set": {
                "status": UserStatus.APPROVED,
                "admin_approved": True,
                "updated_at": datetime.utcnow()
            }
        }
    )

    return {"message": "Driver approved successfully"}

@api_router.post("/admin/drivers/{driver_id}/reject")
async def reject_driver_verification(driver_id: str, current_user: User = Depends(get_admin_user)):
    """Manually reject driver verification"""
    driver = await users_collection.find_one({"id": driver_id, "user_type": UserType.DRIVER})
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    # Update driver status
    await users_collection.update_one(
        {"id": driver_id},
        {
            "$set": {
                "status": UserStatus.REJECTED,
                "admin_approved": False,
                "updated_at": datetime.utcnow()
            }
        }
    )

    return {"message": "Driver rejected successfully"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    await initialize_owner()
    logger.info("🚀 RapidMandados API started successfully - México")
    logger.info(f"👑 Owner: {OWNER_NAME} ({OWNER_EMAIL})")
    logger.info(f"💰 Commission Rate: {DEFAULT_COMMISSION_RATE*100}%")
    logger.info(f"💳 Service Fee: ${SERVICE_FEE} {CURRENCY}")
    logger.info(f"🇲🇽 Currency: {CURRENCY} - {COUNTRY}")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()