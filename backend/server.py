--- a/rapidmandados-mexico/backend/server.py
+++ b/rapidmandados-mexico/backend/server.py
@@ -1,13 +1,15 @@
 from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Query, Request
 from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
 from dotenv import load_dotenv
+from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Enum as SQLEnum, Text, ForeignKey
+from sqlalchemy.orm import sessionmaker, declarative_base, relationship
+from sqlalchemy.exc import SQLAlchemyError
 from starlette.middleware.cors import CORSMiddleware
-from motor.motor_asyncio import AsyncIOMotorClient
-from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest
 import os
 import logging
 from pathlib import Path
 from pydantic import BaseModel, Field
+from pydantic_settings import BaseSettings, SettingsConfigDict
 from typing import List, Optional, Dict, Any
 import random
 import string
@@ -17,29 +19,53 @@
 from passlib.context import CryptContext
 from enum import Enum
 import smtplib
-from email.mime.text import MIMEText
-from email.mime.multipart import MIMEMultipart
+# from email.mime.text import MIMEText # Not directly used anymore
+# from email.mime.multipart import MIMEMultipart # Not directly used anymore
 
 ROOT_DIR = Path(__file__).parent
 load_dotenv(ROOT_DIR / '.env')
 
-# Environment variables
-MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
-DB_NAME = os.getenv("DB_NAME", "rapidmandados")
-SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
-OWNER_EMAIL = os.getenv("OWNER_EMAIL", "leonardo.luna@rapidmandados.com")
-OWNER_NAME = os.getenv("OWNER_NAME", "LEONARDO LUNA")
-DEFAULT_COMMISSION_RATE = float(os.getenv("DEFAULT_COMMISSION_RATE", "0.15"))
-SERVICE_FEE = float(os.getenv("SERVICE_FEE", "15.0"))
-PREMIUM_SUBSCRIPTION_MONTHLY = float(os.getenv("PREMIUM_SUBSCRIPTION_MONTHLY", "200.0"))
-STRIPE_API_KEY = os.getenv("STRIPE_API_KEY")
-STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")
+
+# --- Configuration Settings ---
+class Settings(BaseSettings):
+    # Database
+    DATABASE_URL: str = "postgresql://user:password@localhost:5432/rapidmandados"
+
+    # Application
+    SECRET_KEY: str = "your-secret-key-here"
+    OWNER_EMAIL: str = "leonardo.luna@rapidmandados.com"
+    OWNER_NAME: str = "LEONARDO LUNA"
+
+    # Commission
+    DEFAULT_COMMISSION_RATE: float = 0.15
+    SERVICE_FEE: float = 15.0
+    PREMIUM_SUBSCRIPTION_MONTHLY: float = 200.0
+
+    # Email
+    EMAIL_HOST: str = "smtp.gmail.com"
+    EMAIL_PORT: int = 587
+    EMAIL_USER: str = "noreply@rapidmandados.com"
+    EMAIL_PASSWORD: str = ""
+    EMAIL_FROM: str = "RapidMandados <noreply@rapidmandados.com>"
+
+    # Pydantic Settings configuration for loading from .env
+    model_config = SettingsConfigDict(env_file=ROOT_DIR / '.env', extra='ignore')
+
+settings = Settings()
+
+# --- Database Setup (PostgreSQL) ---
+SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL
+
+engine = create_engine(SQLALCHEMY_DATABASE_URL)
+SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
+Base = declarative_base()
+
+# Dependency to get DB session
+def get_db():
+    db = SessionLocal()
+    try:
+        yield db
+    finally:
+        db.close()
 
 # Email configuration for verification
-EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
-EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
-EMAIL_USER = os.getenv("EMAIL_USER", "noreply@rapidmandados.com")
-EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
-EMAIL_FROM = os.getenv("EMAIL_FROM", "RapidMandados <noreply@rapidmandados.com>")
-
-# MongoDB connection
-client = AsyncIOMotorClient(MONGO_URL)
-db = client[DB_NAME]
-
-# Collections
-users_collection = db.users
-orders_collection = db.orders
-commission_config_collection = db.commission_config
-payment_transactions_collection = db.payment_transactions
-driver_payouts_collection = db.driver_payouts
-cash_collections_collection = db.cash_collections
-documents_collection = db.documents
-verification_codes_collection = db.verification_codes
+# EMAIL_HOST = settings.EMAIL_HOST # Already part of settings
+# EMAIL_PORT = settings.EMAIL_PORT
+# EMAIL_USER = settings.EMAIL_USER
+# EMAIL_PASSWORD = settings.EMAIL_PASSWORD
+# EMAIL_FROM = settings.EMAIL_FROM
 
 # Initialize Stripe checkout
-stripe_checkout = None
-if STRIPE_API_KEY:
-    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=None)  # Will be set dynamically
+# Removed Stripe initializations based on previous request to remove Stripe
+# stripe_checkout = None
+# if settings.STRIPE_API_KEY:
+#     stripe_checkout = StripeCheckout(api_key=settings.STRIPE_API_KEY, webhook_url=None)
 
 # Create the main app without a prefix
 app = FastAPI(title="RapidMandados API - México", description="Aplicación de Delivery con Sistema de Comisiones en MXN", version="1.0.0")
@@ -95,7 +121,7 @@
     EXPIRED = "expired"
 
 class PaymentMethod(str, Enum):
-    CREDIT_CARD = "credit_card"
-    CASH = "cash"
+    # Removed: CREDIT_CARD = "credit_card" (as per previous request)
+    CASH = "cash" # Only cash payments for now
 
 class UserStatus(str, Enum):
     PENDING = "pending"
@@ -109,17 +135,14 @@
     EXPIRED = "expired"
 
 class DocumentStatus(str, Enum):
-    PENDING = "pending"
-    APPROVED = "approved"
-    REJECTED = "rejected"
+    PENDING = "pending" # Document submitted, awaiting review
+    APPROVED = "approved" # Document reviewed and approved
+    REJECTED = "rejected" # Document reviewed and rejected
 
 class DocumentType(str, Enum):
     INE = "ine"
-    DRIVERS_LICENSE = "drivers_license"
+    DRIVERS_LICENSE = "drivers_license" # Driver's License
     VEHICLE_REGISTRATION = "vehicle_registration"
     PROOF_OF_ADDRESS = "proof_of_address"
 
-class Document(BaseModel):
-    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
-    user_id: str
-    document_type: DocumentType
-    file_name: str
-    file_data: str  # Base64 encoded
-    upload_date: datetime = Field(default_factory=datetime.utcnow)
-    status: DocumentStatus = DocumentStatus.PENDING
-    admin_comments: Optional[str] = None
-    auto_verified: bool = False
-    verification_confidence: Optional[float] = None
-
-class EmailVerification(BaseModel):
-    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
-    user_id: str
-    email: str
-    verification_code: str
-    status: VerificationStatus = VerificationStatus.PENDING
-    created_at: datetime = Field(default_factory=datetime.utcnow)
-    expires_at: datetime = Field(default_factory=lambda: datetime.utcnow() + timedelta(hours=24))
-    verified_at: Optional[datetime] = None
-    attempts: int = 0
-    max_attempts: int = 3
-
-class DocumentUploadRequest(BaseModel):
-    document_type: DocumentType
-    file_name: str
-    file_data: str  # Base64 encoded
-
-class EmailVerificationRequest(BaseModel):
-    verification_code: str
+
 
 class DriverVerificationStatus(BaseModel):
     email_verified: bool
@@ -137,33 +160,147 @@
     COMPLETED = "completed"
     FAILED = "failed"
 
-class PaymentTransaction(BaseModel):
-    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
-    session_id: Optional[str] = None
-    user_id: Optional[str] = None
-    order_id: Optional[str] = None
-    amount: float
-    currency: str = "mxn"
-    payment_method: PaymentMethod
-    payment_status: PaymentStatus = PaymentStatus.PENDING
-    metadata: Optional[Dict[str, str]] = None
-    created_at: datetime = Field(default_factory=datetime.utcnow)
-    updated_at: datetime = Field(default_factory=datetime.utcnow)
-
-class DriverPayout(BaseModel):
-    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
-    driver_id: str
-    order_id: str
-    amount: float
-    currency: str = "mxn"
-    payment_method: PaymentMethod
-    transfer_status: TransferStatus = TransferStatus.PENDING
-    stripe_transfer_id: Optional[str] = None
-    bank_account: Optional[str] = None
-    created_at: datetime = Field(default_factory=datetime.utcnow)
-    updated_at: datetime = Field(default_factory=datetime.utcnow)
-
-class CashCollection(BaseModel):
-    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
-    driver_id: str
-    order_id: str
-    amount_collected: float
-    commission_owed: float
-    currency: str = "mxn"
-    collection_date: datetime = Field(default_factory=datetime.utcnow)
-    payment_status: PaymentStatus = PaymentStatus.PENDING
-    created_at: datetime = Field(default_factory=datetime.utcnow)
-
-class PaymentTransactionResponse(BaseModel):
-    id: str
-    session_id: str
-    user_id: Optional[str] = None
-    order_id: Optional[str] = None
-    amount: float
-    currency: str
-    payment_status: PaymentStatus
-    metadata: Optional[Dict[str, str]] = None
-    created_at: datetime
-    updated_at: datetime
-
-class CheckoutRequest(BaseModel):
-    order_id: str
-    origin_url: str
-    payment_method: PaymentMethod = PaymentMethod.CREDIT_CARD
+# --- SQLAlchemy Models (Database Tables) ---
+class DBUser(Base): # SQLAlchemy model for User
+    __tablename__ = "users"
+
+    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
+    email = Column(String, unique=True, index=True, nullable=False)
+    name = Column(String, nullable=False)
+    phone = Column(String, nullable=False)
+    user_type = Column(SQLEnum(UserType), nullable=False)
+    password_hash = Column(String, nullable=False)
+    address = Column(String, nullable=True)
+    status = Column(SQLEnum(UserStatus), default=UserStatus.PENDING, nullable=False)
+    is_phone_verified = Column(Boolean, default=False, nullable=False)
+    is_email_verified = Column(Boolean, default=False, nullable=False)
+    phone_verification_code = Column(String, nullable=True)
+    email_verification_code = Column(String, nullable=True)
+    verification_code_expires = Column(DateTime, nullable=True)
+    documents_uploaded = Column(Boolean, default=False, nullable=False)
+    admin_approved = Column(Boolean, default=False, nullable=False)
+    admin_comments = Column(String, nullable=True)
+    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
+    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
+    is_premium = Column(Boolean, default=False, nullable=False)
+    premium_expires_at = Column(DateTime, nullable=True)
+    commission_rate = Column(Float, nullable=True)
+    is_active = Column(Boolean, default=True, nullable=False)
+    total_orders = Column(Integer, default=0, nullable=False)
+    total_earnings = Column(Float, default=0.0, nullable=False)
+
+    orders_client = relationship("DBOrder", back_populates="client_user", foreign_keys="DBOrder.client_id")
+    orders_driver = relationship("DBOrder", back_populates="driver_user", foreign_keys="DBOrder.driver_id")
+    documents = relationship("DBDocument", back_populates="user")
+    email_verifications = relationship("DBEmailVerification", back_populates="user")
+    payments = relationship("DBPaymentTransaction", back_populates="user")
+    payouts = relationship("DBDriverPayout", back_populates="driver")
+    cash_collections = relationship("DBCashCollection", back_populates="driver")
+
+class DBOrder(Base):
+    __tablename__ = "orders"
+
+    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
+    client_id = Column(String, ForeignKey("users.id"), nullable=False)
+    driver_id = Column(String, ForeignKey("users.id"), nullable=True)
+    title = Column(String, nullable=False)
+    description = Column(Text, nullable=False)
+    pickup_address = Column(String, nullable=False)
+    delivery_address = Column(String, nullable=False)
+    price = Column(Float, nullable=False) # Base price of the order item/service
+    status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
+    payment_status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
+    payment_method = Column(SQLEnum(PaymentMethod), nullable=True) # Cash or Credit Card
+    financials = Column(Text, nullable=True) # Storing OrderFinancials as JSON string
+    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
+    accepted_at = Column(DateTime, nullable=True)
+    delivered_at = Column(DateTime, nullable=True)
+    stripe_payment_intent = Column(String, nullable=True) # Kept for potential future use, not currently used
+
+    client_user = relationship("DBUser", back_populates="orders_client", foreign_keys=[client_id])
+    driver_user = relationship("DBUser", back_populates="orders_driver", foreign_keys=[driver_id])
+
+class DBPaymentTransaction(Base):
+    __tablename__ = "payment_transactions"
+
+    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
+    session_id = Column(String, nullable=True) # For Stripe, if reintroduced
+    user_id = Column(String, ForeignKey("users.id"), nullable=True)
+    order_id = Column(String, nullable=True) # Not a foreign key if order might be deleted
+    amount = Column(Float, nullable=False)
+    currency = Column(String, default="mxn", nullable=False)
+    payment_method = Column(SQLEnum(PaymentMethod), nullable=False)
+    payment_status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
+    metadata = Column(Text, nullable=True) # Storing metadata as JSON string
+    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
+    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
+
+    user = relationship("DBUser", back_populates="payments")
+
+class DBDriverPayout(Base):
+    __tablename__ = "driver_payouts"
+
+    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
+    driver_id = Column(String, ForeignKey("users.id"), nullable=False)
+    order_id = Column(String, ForeignKey("orders.id"), nullable=False)
+    amount = Column(Float, nullable=False)
+    currency = Column(String, default="mxn", nullable=False)
+    payment_method = Column(SQLEnum(PaymentMethod), nullable=False)
+    transfer_status = Column(SQLEnum(TransferStatus), default=TransferStatus.PENDING, nullable=False)
+    stripe_transfer_id = Column(String, nullable=True) # Kept for future, not used for cash
+    bank_account = Column(String, nullable=True) # Placeholder for driver bank details
+    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
+    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
+
+    driver = relationship("DBUser", back_populates="payouts")
+    order = relationship("DBOrder") # One-to-one or one-to-many from order
+
+class DBCashCollection(Base):
+    __tablename__ = "cash_collections"
+
+    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
+    driver_id = Column(String, ForeignKey("users.id"), nullable=False)
+    order_id = Column(String, ForeignKey("orders.id"), nullable=False)
+    amount_collected = Column(Float, nullable=False) # Total cash driver collected from client
+    commission_owed = Column(Float, nullable=False) # Amount driver owes to owner
+    currency = Column(String, default="mxn", nullable=False)
+    collection_date = Column(DateTime, default=datetime.utcnow, nullable=False)
+    payment_status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False) # Status of commission owed to owner
+    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
+
+    driver = relationship("DBUser", back_populates="cash_collections")
+    order = relationship("DBOrder") # One-to-one or one-to-many from order
+
+class DBDocument(Base):
+    __tablename__ = "documents"
+
+    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
+    user_id = Column(String, ForeignKey("users.id"), nullable=False)
+    document_type = Column(SQLEnum(DocumentType), nullable=False)
+    file_name = Column(String, nullable=False)
+    file_data = Column(Text, nullable=False) # Base64 encoded file content
+    upload_date = Column(DateTime, default=datetime.utcnow, nullable=False)
+    status = Column(SQLEnum(DocumentStatus), default=DocumentStatus.PENDING, nullable=False)
+    admin_comments = Column(String, nullable=True)
+    auto_verified = Column(Boolean, default=False, nullable=False)
+    verification_confidence = Column(Float, nullable=True)
+
+    user = relationship("DBUser", back_populates="documents")
+
+class DBEmailVerification(Base):
+    __tablename__ = "email_verifications" # Changed from verification_codes as it's email specific
+
+    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
+    user_id = Column(String, ForeignKey("users.id"), nullable=False)
+    email = Column(String, nullable=False)
+    verification_code = Column(String, nullable=False)
+    status = Column(SQLEnum(VerificationStatus), default=VerificationStatus.PENDING, nullable=False)
+    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
+    expires_at = Column(DateTime, nullable=False)
+    verified_at = Column(DateTime, nullable=True)
+    attempts = Column(Integer, default=0, nullable=False)
+    max_attempts = Column(Integer, default=3, nullable=False)
+
+    user = relationship("DBUser", back_populates="email_verifications")
+
+class DBCommissionConfig(Base):
+    __tablename__ = "commission_config"
+
+    id = Column(Integer, primary_key=True, autoincrement=True) # Simple ID for config
+    commission_rate = Column(Float, nullable=False)
+    service_fee = Column(Float, nullable=False)
+    premium_subscription_monthly = Column(Float, nullable=False)
+    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
+    updated_by = Column(String, nullable=True) # User ID who last updated
 
 class CashPaymentRequest(BaseModel):
     order_id: str
@@ -176,14 +313,22 @@
     INACTIVE = "inactive"
     EXPIRED = "expired"
 
-# Models
-class User(BaseModel):
-    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
-    email: str
-    name: str
-    phone: str
-    user_type: UserType
-    password_hash: str
+# --- Pydantic Models (for API Request/Response) ---
+# Pydantic model for User (for API I/O), corresponds to DBUser
+class User(BaseModel): 
+    id: Optional[str] = None
+    email: str
+    name: str
+    phone: str
+    user_type: UserType
+    password_hash: Optional[str] = None # Should not be sent directly in responses
+    
+    # Optional fields from DBUser
     address: str
     status: UserStatus = UserStatus.PENDING
     is_phone_verified: bool = False
     is_email_verified: bool = False
@@ -198,16 +343,71 @@
     is_active: bool = True
     total_orders: int = 0
     total_earnings: float = 0.0
-
+    
+    # Configuration for Pydantic to work with SQLAlchemy models
+    class Config:
+        from_attributes = True # Was orm_mode = True in older Pydantic
+
+# Pydantic model for Order (for API I/O), corresponds to DBOrder
+class Order(BaseModel):
+    id: Optional[str] = None
+    client_id: str
+    driver_id: Optional[str] = None
+    title: str
+    description: str
+    pickup_address: str
+    delivery_address: str
+    price: float
+    status: OrderStatus = OrderStatus.PENDING
+    payment_status: PaymentStatus = PaymentStatus.PENDING
+    payment_method: Optional[PaymentMethod] = PaymentMethod.CASH
+    financials: Optional[Dict[str, Any]] = None # Use Dict or specific Pydantic model
+    created_at: Optional[datetime] = None
+    accepted_at: Optional[datetime] = None
+    delivered_at: Optional[datetime] = None
+    stripe_payment_intent: Optional[str] = None
+
+    class Config:
+        from_attributes = True
+
+# Pydantic model for PaymentTransaction (for API I/O), corresponds to DBPaymentTransaction
+class PaymentTransaction(BaseModel):
+    id: Optional[str] = None
+    session_id: Optional[str] = None
+    user_id: Optional[str] = None
+    order_id: Optional[str] = None
+    amount: float
+    currency: str = "mxn"
+    payment_method: PaymentMethod
+    payment_status: PaymentStatus = PaymentStatus.PENDING
+    metadata: Optional[Dict[str, str]] = None
+    created_at: Optional[datetime] = None
+    updated_at: Optional[datetime] = None
+
+    class Config:
+        from_attributes = True
+
+# Pydantic model for DriverPayout (for API I/O), corresponds to DBDriverPayout
+class DriverPayout(BaseModel):
+    id: Optional[str] = None
+    driver_id: str
+    order_id: str
+    amount: float
+    currency: str = "mxn"
+    payment_method: PaymentMethod
+    transfer_status: TransferStatus = TransferStatus.PENDING
+    stripe_transfer_id: Optional[str] = None
+    bank_account: Optional[str] = None
+    created_at: Optional[datetime] = None
+    updated_at: Optional[datetime] = None
+
+    class Config:
+        from_attributes = True
+
 class UserCreate(BaseModel):
     email: str
     name: str
     phone: str
     password: str
@@ -215,22 +415,21 @@
     address: Optional[str] = None
 
 class UserLogin(BaseModel):
-    email: str
-    password: str
-
-class UserResponse(BaseModel):
-    id: str
-    email: str
-    name: str
-    phone: str
-    user_type: UserType
-    address: Optional[str] = None
-    is_premium: bool = False
-    premium_expires_at: Optional[datetime] = None
-    total_orders: int = 0
-    total_earnings: float = 0.0
-
-class OrderFinancials(BaseModel):
+    email: str # No changes from previous version
+    password: str # No changes from previous version
+
+class UserResponse(BaseModel): # Adapted to new DBUser model
+    id: str
+    email: str
+    name: str
+    phone: str
+    user_type: UserType
+    address: Optional[str] = None
+    is_premium: bool = False
+    premium_expires_at: Optional[datetime] = None
+    total_orders: int = 0
+    total_earnings: float = 0.0
+
+class OrderFinancials(BaseModel): # Remains Pydantic, stored as JSON string in DB
     subtotal: float
     service_fee: float
     iva_amount: float
@@ -240,24 +439,18 @@
     owner_earnings: float
     total_amount: float
 
-class Order(BaseModel):
-    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
-    client_id: str
-    driver_id: Optional[str] = None
-    title: str
-    description: str
-    pickup_address: str
-    delivery_address: str
-    price: float
-    status: OrderStatus = OrderStatus.PENDING
-    payment_status: PaymentStatus = PaymentStatus.PENDING
-    financials: Optional[OrderFinancials] = None
-    created_at: datetime = Field(default_factory=datetime.utcnow)
-    accepted_at: Optional[datetime] = None
-    delivered_at: Optional[datetime] = None
-    stripe_payment_intent: Optional[str] = None
-
-class OrderCreate(BaseModel):
+class DocumentUploadRequest(BaseModel): # Pydantic model for document upload request
+    document_type: DocumentType
+    file_name: str
+    file_data: str # Base64 encoded file content
+
+class EmailVerificationRequest(BaseModel): # Pydantic model for email verification request
+    verification_code: str
+
+# Pydantic model for OrderCreate (for API input)
+class OrderCreate(BaseModel): 
     title: str
     description: str
     pickup_address: str
@@ -265,19 +458,19 @@
     price: float
 
 class OrderResponse(BaseModel):
-    id: str
-    client_id: str
+    id: str # Will be generated by DB
+    client_id: str 
     client_name: str
     driver_id: Optional[str] = None
     driver_name: Optional[str] = None
     title: str
     description: str
     pickup_address: str
-    delivery_address: str
+    delivery_address: str # No change from previous version
     price: float
     status: OrderStatus
     payment_status: PaymentStatus
-    financials: Optional[OrderFinancials] = None
+    payment_method: Optional[PaymentMethod] = None # Added payment method to response
     created_at: datetime
     accepted_at: Optional[datetime] = None
     delivered_at: Optional[datetime] = None
@@ -291,7 +484,7 @@
     monthly_revenue: float
     monthly_commission: float
     average_order_value: float
-
+# Pydantic model for CommissionConfig (for API input/output)
 class CommissionConfig(BaseModel):
     commission_rate: float
     service_fee: float
@@ -318,17 +511,19 @@
     encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
     return encoded_jwt
 
-async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
-    try:
+def get_current_user(db: Session = Depends(get_db), credentials: HTTPAuthorizationCredentials = Depends(security)):
+    try: # Check token validity
         token = credentials.credentials
-        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
+        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
         user_id: str = payload.get("sub")
         if user_id is None:
             raise HTTPException(status_code=401, detail="Invalid token")
     except jwt.PyJWTError:
         raise HTTPException(status_code=401, detail="Invalid token")
     
-    user = await db.users.find_one({"id": user_id})
-    if user is None:
+    # Query the user from the database
+    user = db.query(DBUser).filter(DBUser.id == user_id).first()
+    if user is None: # User not found in DB
         raise HTTPException(status_code=401, detail="User not found")
-    return User(**user)
-
-async def get_admin_user(current_user: User = Depends(get_current_user)):
+    return User.model_validate(user) # Use .model_validate for Pydantic v2
+
+def get_admin_user(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
     if current_user.user_type != UserType.ADMIN:
         raise HTTPException(status_code=403, detail="Admin access required")
     return current_user
@@ -336,11 +531,11 @@
 async def create_driver_payout_for_order(order_id: str):
     """Create a driver payout record when an order is paid"""
     # Get the order details
-    order = await orders_collection.find_one({"id": order_id})
+    order = db.query(DBOrder).filter(DBOrder.id == order_id).first() # Use db session
     if not order or not order.get("driver_id"):
         return  # No driver assigned yet or order not found
     
     # Check if payout already exists
-    existing_payout = await driver_payouts_collection.find_one({"order_id": order_id})
+    existing_payout = db.query(DBDriverPayout).filter(DBDriverPayout.order_id == order_id).first()
     if existing_payout:
         return  # Payout already created
     
@@ -353,19 +548,21 @@
         driver_id=order["driver_id"],
         order_id=order_id,
         amount=driver_earnings,
         currency="mxn",
-        payment_method=PaymentMethod.CREDIT_CARD,
+        payment_method=PaymentMethod.CASH, # Always cash for driver payouts in this version
         transfer_status=TransferStatus.PENDING
     )
-    
-    await driver_payouts_collection.insert_one(driver_payout.dict())
+
+    db_payout = DBDriverPayout(**driver_payout.dict(exclude_unset=True))
+    db.add(db_payout)
+    db.commit()
+
 
 # Initialize owner account
 async def initialize_owner():
     """Create owner account if it doesn't exist"""
-    owner = await db.users.find_one({"email": OWNER_EMAIL})
+    db = SessionLocal() # Get a new session for startup event
+    owner = db.query(DBUser).filter(DBUser.email == settings.OWNER_EMAIL).first()
     if not owner:
         owner_user = User(
-            email=OWNER_EMAIL,
-            name=OWNER_NAME,
+            email=settings.OWNER_EMAIL,
+            name=settings.OWNER_NAME,
             phone="+52 55 0000 0000",
             user_type=UserType.ADMIN,
             password_hash=hash_password("owner123456"),
@@ -375,12 +572,13 @@
             is_email_verified=True,
             admin_approved=True,
             documents_uploaded=True
-        )
-        await db.users.insert_one(owner_user.dict())
-        print(f"✅ Owner account created: {OWNER_NAME} - {OWNER_EMAIL}")
+        ) # Pydantic model
+        db_owner = DBUser(**owner_user.dict(exclude_unset=True)) # Convert to SQLAlchemy model
+        db.add(db_owner)
+        db.commit()
+        print(f"✅ Owner account created: {settings.OWNER_NAME} - {settings.OWNER_EMAIL}")
     else:
-        # Update existing owner to have all required fields
-        await db.users.update_one(
-            {"email": OWNER_EMAIL},
-            {
-                "$set": {
+        # Update existing owner to have all required fields (using SQLAlchemy syntax)
+        db.query(DBUser).filter(DBUser.email == settings.OWNER_EMAIL).update(
+            {
+                "status": UserStatus.APPROVED,
+                "is_phone_verified": True,
+                "is_email_verified": True,
+                "admin_approved": True,
+                "documents_uploaded": True,
+                "updated_at": datetime.utcnow()
+            },
+            synchronize_session="fetch"
+        )
+        db.commit()
+        print(f"✅ Owner account updated: {settings.OWNER_NAME} - {settings.OWNER_EMAIL}")
+    db.close() # Close session used for startup
+
+# Routes
+def generate_verification_code():
+    """Generate a 6-digit verification code"""
+    return ''.join(random.choices(string.digits, k=6))
+
+async def send_email_verification(email: str, code: str, user_name: str):
+    """Send email verification code"""
+    try: # Mock email sending for now
+        # Create email message
+        subject = "🚚 RapidMandados - Código de Verificación"
+        body = f"""
+        ¡Hola {user_name}!
+        
+        Tu código de verificación para RapidMandados es:
+        
+        {code}
+        
+        Este código expirará en 24 horas.
+        
+        Si no solicitaste este código, ignora este mensaje.
+        
+        Equipo RapidMandados México
+        """
+        
+        # For now, we'll just log the verification code
+        # In production, you would integrate with an email service
+        print(f"📧 Email verification code for {email}: {code}")
+        print(f"📧 Email content: {body}")
+        
+        # TODO: Integrate with actual email service (SendGrid, AWS SES, etc.)
+        return True
+        
+    except Exception as e:
+        print(f"❌ Error sending email to {email}: {e}")
+        return False
+
+async def validate_document_automatically(document_type: DocumentType, file_data: str):
+    """Automatically validate document based on type and content"""
+    # For now, we'll do basic validation
+    # In production, you would integrate with OCR and document validation services
+    
+    validation_results = {
+        "is_valid": True,
+        "confidence": 0.95,
+        "extracted_data": {},
+        "issues": []
+    }
+    
+    try:
+        # Basic file validation
+        if not file_data or len(file_data) < 100:
+            validation_results["is_valid"] = False
+            validation_results["confidence"] = 0.0
+            validation_results["issues"].append("Archivo muy pequeño o inválido")
+            return validation_results
+        
+        # Document type specific validation
+        if document_type == DocumentType.INE:
+            validation_results["extracted_data"] = {
+                "document_type": "INE",
+                "status": "Validación automática completada"
+            }
+        elif document_type == DocumentType.DRIVERS_LICENSE:
+            validation_results["extracted_data"] = {
+                "document_type": "Licencia de Conducir",
+                "status": "Validación automática completada"
+            }
+        
+        # Simulate high confidence for demo
+        validation_results["confidence"] = 0.92
+        
+        print(f"📄 Document validation completed for {document_type.value}: {validation_results['confidence']:.2f} confidence")
+        
+        return validation_results
+        
+    except Exception as e:
+        print(f"❌ Error validating document: {e}")
+        validation_results["is_valid"] = False
+        validation_results["confidence"] = 0.0
+        validation_results["issues"].append(f"Error en validación: {str(e)}")
+        return validation_results
+
+def check_driver_verification_status(user_id: str, db: Session):
+    """Check complete verification status for a driver"""
+    user = db.query(DBUser).filter(DBUser.id == user_id).first()
+    if not user:
+        return None
+    
+    # Check email verification
+    email_verified = user.is_email_verified # Access attribute directly
+    
+    # Check required documents
+    required_docs = [DocumentType.INE, DocumentType.DRIVERS_LICENSE]
+    documents_status = {}
+    
+    for doc_type in required_docs:
+        doc = db.query(DBDocument).filter(DBDocument.user_id == user_id, DBDocument.document_type == doc_type).first()
+        if doc:
+            documents_status[doc_type.value] = DocumentStatus(doc.status)
+        else:
+            documents_status[doc_type.value] = DocumentStatus.PENDING
+    
+    # Check if all documents are approved
+    all_docs_approved = all(
+        status == DocumentStatus.APPROVED 
+        for status in documents_status.values()
+    )
+    
+    # Overall verification complete
+    overall_complete = email_verified and all_docs_approved
+    
+    # Can accept orders
+    can_accept_orders = overall_complete and user.status == UserStatus.APPROVED
+    
+    # Pending actions
+    pending_actions = []
+    if not email_verified:
+        pending_actions.append("Verificar correo electrónico")
+    
+    for doc_type, status in documents_status.items():
+        if status == DocumentStatus.PENDING:
+            pending_actions.append(f"Subir documento: {doc_type.value}")
+        elif status == DocumentStatus.REJECTED:
+            pending_actions.append(f"Volver a subir documento: {doc_type.value}")
+    
+    return DriverVerificationStatus(
+        email_verified=email_verified,
+        documents_status=documents_status,
+        overall_verification_complete=overall_complete,
+        can_accept_orders=can_accept_orders,
+        pending_actions=pending_actions
+    )
+
+async def send_phone_verification(phone: str, code: str):
+    """Send SMS verification code (mock implementation)"""
+    # In production, integrate with SMS service like Twilio
+    print(f"📱 SMS sent to {phone}: Your verification code is {code}")
+    return True
+
+
+@api_router.post("/auth/register", response_model=dict)
+async def register(user_data: UserCreate, db: Session = Depends(get_db)):
+    # Check if user exists
+    existing_user = db.query(DBUser).filter(DBUser.email == user_data.email).first()
+    if existing_user:
+        raise HTTPException(status_code=400, detail="Email already registered")
+    
+    # Create user - simplified for immediate functionality
+    user = User( # Pydantic model for input
+        email=user_data.email,
+        name=user_data.name,
+        phone=user_data.phone,
+        user_type=user_data.user_type,
+        password_hash=hash_password(user_data.password),
+        address=user_data.address,
+        status=UserStatus.APPROVED,  # Approve immediately for now
+        is_phone_verified=True,      # Skip verification for now
+        is_email_verified=True,      # Skip verification for now
+        admin_approved=True,         # Auto-approve
+        documents_uploaded=True      # Skip documents for now
+    )
+    
+    db_user = DBUser(**user.model_dump(exclude_unset=True)) # Convert Pydantic to SQLAlchemy model
+    db.add(db_user)
+    try:
+        db.commit()
+        db.refresh(db_user) # Refresh to get auto-generated ID
+    except SQLAlchemyError as e:
+        db.rollback()
+        raise HTTPException(status_code=500, detail=f"Database error: {e}")
+    
+    # Create JWT token for immediate login
+    token = create_access_token(data={"sub": db_user.id})
+    
+    return {
+        "access_token": token,
+        "token_type": "bearer",
+        "user": UserResponse.model_validate(db_user).model_dump(), # Use model_validate and model_dump for Pydantic v2
+        "message": "Registration successful"
+    }
+
+@api_router.post("/auth/verify-phone")
+async def verify_phone(verification_data: dict, db: Session = Depends(get_db)):
+    """Verify phone number with code"""
+    user_id = verification_data.get("user_id")
+    phone_code = verification_data.get("phone_code")
+    
+    if not user_id or not phone_code:
+        raise HTTPException(status_code=400, detail="User ID and phone code are required")
+    
+    # Get user
+    user = db.query(DBUser).filter(DBUser.id == user_id).first()
+    if not user:
+        raise HTTPException(status_code=404, detail="User not found")
+    
+    # Check if code is valid and not expired
+    if (user.phone_verification_code != phone_code or 
+        user.verification_code_expires < datetime.utcnow()):
+        raise HTTPException(status_code=400, detail="Invalid or expired verification code")
+    
+    # Update user as phone verified
+    user.is_phone_verified = True
+    user.phone_verification_code = None
+    user.updated_at = datetime.utcnow()
+    db.add(user)
+    db.commit()
+    db.refresh(user)
+    
+    return {"message": "Phone verified successfully"}
+
+@api_router.post("/auth/verify-email")
+async def verify_email(verification_data: dict, db: Session = Depends(get_db)):
+    """Verify email with code"""
+    user_id = verification_data.get("user_id")
+    email_code = verification_data.get("email_code")
+    
+    if not user_id or not email_code:
+        raise HTTPException(status_code=400, detail="User ID and email code are required")
+    
+    # Get verification record
+    verification_record = db.query(DBEmailVerification).filter(DBEmailVerification.user_id == user_id, DBEmailVerification.status == VerificationStatus.PENDING).first()
+    if not verification_record:
+        raise HTTPException(status_code=404, detail="No pending email verification found for this user.")
+
+    # Check expiration
+    if datetime.utcnow() > verification_record.expires_at:
+        verification_record.status = VerificationStatus.EXPIRED
+        db.add(verification_record)
+        db.commit()
+        db.refresh(verification_record)
+        raise HTTPException(status_code=400, detail="Verification code expired")
+
+    # Check attempts
+    if verification_record.attempts >= verification_record.max_attempts:
+        verification_record.status = VerificationStatus.FAILED
+        db.add(verification_record)
+        db.commit()
+        db.refresh(verification_record)
+        raise HTTPException(status_code=400, detail="Maximum attempts exceeded for verification code.")
+
+    # Verify code
+    if verification_record.verification_code != email_code:
+        verification_record.attempts += 1
+        db.add(verification_record)
+        db.commit()
+        db.refresh(verification_record)
+        raise HTTPException(status_code=400, detail="Invalid verification code.")
+
+    # Mark as verified
+    verification_record.status = VerificationStatus.VERIFIED
+    verification_record.verified_at = datetime.utcnow()
+    db.add(verification_record)
+    db.commit()
+    db.refresh(verification_record)
+    
+    # Update user's email_verified status
+    user = db.query(DBUser).filter(DBUser.id == user_id).first()
+    if user:
+        user.is_email_verified = True
+        user.updated_at = datetime.utcnow()
+        db.add(user)
+        db.commit()
+        db.refresh(user)
+    
+    return {"message": "Email verified successfully"}
+
+@api_router.post("/auth/upload-document")
+async def upload_document(document_data: DocumentUploadRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
+    """Upload required documents for driver verification"""
+    
+    if current_user.user_type != UserType.DRIVER:
+        raise HTTPException(status_code=403, detail="Only drivers can upload documents.")
+
+    # Check if user is verified
+    if not current_user.is_phone_verified or not current_user.is_email_verified:
+        raise HTTPException(status_code=400, detail="Please verify phone and email first.")
+    
+    # Check if document already exists
+    existing_doc = db.query(DBDocument).filter(DBDocument.user_id == current_user.id, DBDocument.document_type == document_data.document_type).first()
+    
+    if existing_doc and existing_doc.status == DocumentStatus.APPROVED:
+        raise HTTPException(status_code=400, detail="Document already approved.")
+    
+    # Validate document automatically (mock logic)
+    validation_result = await validate_document_automatically(document_data.document_type, document_data.file_data)
+    
+    # Create or update document record
+    if existing_doc:
+        existing_doc.file_name = document_data.file_name
+        existing_doc.file_data = document_data.file_data
+        existing_doc.upload_date = datetime.utcnow()
+        existing_doc.status = DocumentStatus.APPROVED if validation_result["is_valid"] else DocumentStatus.REJECTED
+        existing_doc.auto_verified = True
+        existing_doc.verification_confidence = validation_result["confidence"]
+        db.add(existing_doc)
+    else:
+        new_document = DBDocument(
+            user_id=current_user.id,
+            document_type=document_data.document_type,
+            file_name=document_data.file_name,
+            file_data=document_data.file_data,
+            status=DocumentStatus.APPROVED if validation_result["is_valid"] else DocumentStatus.REJECTED,
+            auto_verified=True,
+            verification_confidence=validation_result["confidence"]
+        )
+        db.add(new_document)
+    
+    try:
+        db.commit()
+        if not existing_doc: db.refresh(new_document)
+    except SQLAlchemyError as e:
+        db.rollback()
+        raise HTTPException(status_code=500, detail=f"Database error saving document: {e}")
+    
+    # Check if user has uploaded both required documents (INE and DRIVERS_LICENSE)
+    user_documents = db.query(DBDocument).filter(DBDocument.user_id == current_user.id).all()
+    document_types_uploaded = {doc.document_type for doc in user_documents}
+
+    if DocumentType.INE in document_types_uploaded and DocumentType.DRIVERS_LICENSE in document_types_uploaded:
+        # Mark user as having uploaded documents
+        current_user.documents_uploaded = True
+        current_user.updated_at = datetime.utcnow()
+        db.add(current_user)
+        try:
+            db.commit()
+            db.refresh(current_user)
+        except SQLAlchemyError as e:
+            db.rollback()
+            raise HTTPException(status_code=500, detail=f"Database error updating user document status: {e}")
+    
+    return {"message": "Document uploaded successfully", "document_status": document.status if existing_doc else new_document.status}
+
+@api_router.get("/admin/pending-drivers", response_model=List[UserResponse]) # Changed response model to UserResponse list
+async def get_pending_drivers(db: Session = Depends(get_db), current_user: User = Depends(get_admin_user)):
+    """Get all drivers pending approval"""
+    # Query drivers who are pending and have uploaded documents
+    drivers = db.query(DBUser).filter(
+        DBUser.user_type == UserType.DRIVER,
+        DBUser.status == UserStatus.PENDING,
+        DBUser.documents_uploaded == True
+    ).all()
+    
+    # Enrich with document info (for display, will be handled by frontend)
+    # The UserResponse model will simplify this. Documents are now separate endpoint.
+    return [UserResponse.model_validate(driver) for driver in drivers]
+
+@api_router.post("/admin/approve-driver/{driver_id}")
+async def approve_driver(driver_id: str, approval_data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_admin_user)):
+    """Approve or reject a driver"""
+    approved = approval_data.get("approved", False)
+    comments = approval_data.get("comments", None)
+    
+    # Get driver
+    driver = db.query(DBUser).filter(DBUser.id == driver_id, DBUser.user_type == UserType.DRIVER).first()
+    if not driver:
+        raise HTTPException(status_code=404, detail="Driver not found")
+    
+    # Update driver status
+    driver.status = UserStatus.APPROVED if approved else UserStatus.REJECTED
+    driver.admin_approved = approved
+    driver.admin_comments = comments
+    driver.updated_at = datetime.utcnow()
+    db.add(driver)
+    try:
+        db.commit()
+        db.refresh(driver)
+    except SQLAlchemyError as e:
+        db.rollback()
+        raise HTTPException(status_code=500, detail=f"Database error approving driver: {e}")
+    
+    action = "approved" if approved else "rejected"
+    return {"message": f"Driver {action} successfully"}
+
+@api_router.post("/auth/login", response_model=dict)
+async def login(user_data: UserLogin, db: Session = Depends(get_db)):
+    # Find user by email
+    user = db.query(DBUser).filter(DBUser.email == user_data.email).first()
+    if not user:
+        raise HTTPException(status_code=401, detail="Invalid credentials")
+    
+    # Verify password
+    if not verify_password(user_data.password, user.password_hash):
+        raise HTTPException(status_code=401, detail="Invalid credentials")
+    
+    # Create access token
+    access_token = create_access_token(data={"sub": user.id})
+    
+    return {
+        "access_token": access_token,
+        "token_type": "bearer",
+        "user": UserResponse.model_validate(user).model_dump()
+    }
+
+@api_router.get("/auth/me", response_model=UserResponse)
+async def get_me(current_user: User = Depends(get_current_user)):
+    return current_user # Already a Pydantic model
+
+@api_router.post("/orders", response_model=OrderResponse)
+async def create_order(order_data: OrderCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
+    if current_user.user_type != UserType.CLIENT:
+        raise HTTPException(status_code=403, detail="Only clients can create orders")
+    
+    # Validate order price
+    if order_data.price < MIN_ORDER_VALUE or order_data.price > MAX_ORDER_VALUE:
+        raise HTTPException(
+            status_code=400, 
+            detail=f"Order price must be between ${MIN_ORDER_VALUE:,.2f} and ${MAX_ORDER_VALUE:,.2f} MXN"
+        )
+    
+    # Calculate financials
+    financials = calculate_order_financials(order_data.price)
+    
+    order = Order( # Pydantic Order model
+        client_id=current_user.id,
+        title=order_data.title,
+        description=order_data.description,
+        pickup_address=order_data.pickup_address,
+        delivery_address=order_data.delivery_address,
+        price=order_data.price,
+        financials=financials.model_dump(), # Convert Pydantic to dict for storage
+        payment_method=PaymentMethod.CASH, # Default to cash as per previous request
+        payment_status=PaymentStatus.PENDING # Cash payments start as pending
+    )
+    
+    db_order = DBOrder(**order.model_dump(exclude_unset=True)) # Convert Pydantic to SQLAlchemy model
+    db.add(db_order)
+    try:
+        db.commit()
+        db.refresh(db_order)
+    except SQLAlchemyError as e:
+        db.rollback()
+        raise HTTPException(status_code=500, detail=f"Database error creating order: {e}")
+    
+    # Update client stats
+    current_user_db = db.query(DBUser).filter(DBUser.id == current_user.id).first()
+    if current_user_db:
+        current_user_db.total_orders += 1
+        db.add(current_user_db)
+        db.commit()
+        db.refresh(current_user_db)
+    
+    return OrderResponse(
+        **Order.model_validate(db_order).model_dump(), # Validate from DB model and dump
+        client_name=current_user.name,
+        driver_name=None
+    )
+
+@api_router.get("/orders", response_model=List[OrderResponse])
+async def get_orders(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
+    if current_user.user_type == UserType.CLIENT:
+        # Get client's orders
+        orders = db.query(DBOrder).filter(DBOrder.client_id == current_user.id).all()
+    elif current_user.user_type == UserType.DRIVER:
+        # Get available orders for drivers (status PENDING or ACCEPTED, not assigned to another driver)
+        orders = db.query(DBOrder).filter(DBOrder.status.in_([OrderStatus.PENDING, OrderStatus.ACCEPTED]), DBOrder.driver_id == None).all()
+    else:  # ADMIN
+        # Get all orders for admin
+        orders = db.query(DBOrder).all()
+    
+    order_responses = []
+    for order in orders:
+        # Get client info
+        client = db.query(DBUser).filter(DBUser.id == order.client_id).first()
+        client_name = client.name if client else "Unknown"
+        
+        # Get driver info if exists
+        driver_name = None
+        if order.driver_id:
+            driver = db.query(DBUser).filter(DBUser.id == order.driver_id).first()
+            driver_name = driver.name if driver else "Unknown"
+        
+        # Ensure payment_status and payment_method are set for backward compatibility
+        order_data = Order.model_validate(order).model_dump() # Convert DB model to Pydantic dict
+        if "payment_status" not in order_data:
+            order_data["payment_status"] = PaymentStatus.PENDING
+        if "payment_method" not in order_data:
+            order_data["payment_method"] = PaymentMethod.CASH # Default to cash for old orders
+            
+        order_responses.append(OrderResponse(
+            **order_data,
+            client_name=client_name,
+            driver_name=driver_name
+        ))
+    
+    return order_responses
+
+@api_router.get("/orders/driver", response_model=List[OrderResponse])
+async def get_driver_orders(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
+    if current_user.user_type != UserType.DRIVER:
+        raise HTTPException(status_code=403, detail="Only drivers can access this endpoint")
+    
+    # Get driver's accepted orders
+    orders = db.query(DBOrder).filter(DBOrder.driver_id == current_user.id).all()
+    
+    order_responses = []
+    for order in orders:
+        # Get client info
+        client = db.query(DBUser).filter(DBUser.id == order.client_id).first()
+        client_name = client.name if client else "Unknown"
+        
+        # Ensure payment_status and payment_method are set for backward compatibility
+        order_data = Order.model_validate(order).model_dump()
+        if "payment_status" not in order_data:
+            order_data["payment_status"] = PaymentStatus.PENDING
+        if "payment_method" not in order_data:
+            order_data["payment_method"] = PaymentMethod.CASH # Default to cash for old orders
+            
+        order_responses.append(OrderResponse(
+            **order_data,
+            client_name=client_name,
+            driver_name=current_user.name
+        ))
+    
+    return order_responses
+
+@api_router.put("/orders/{order_id}/accept")
+async def accept_order(order_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
+    if current_user.user_type != UserType.DRIVER:
+        raise HTTPException(status_code=403, detail="Only drivers can accept orders")
+    
+    # Check driver verification status
+    verification_status = check_driver_verification_status(current_user.id, db) # Pass db session
+    if not verification_status or not verification_status.can_accept_orders:
+        raise HTTPException(
+            status_code=403, 
+            detail="Driver not fully verified. Complete verification process to accept orders."
+        )
+    
+    # Find order
+    order = db.query(DBOrder).filter(DBOrder.id == order_id).first()
+    if not order:
+        raise HTTPException(status_code=404, detail="Order not found")
+    
+    if order.status != OrderStatus.PENDING:
+        raise HTTPException(status_code=400, detail="Order is not available")
+    
+    # Update order
+    order.driver_id = current_user.id
+    order.status = OrderStatus.ACCEPTED
+    order.accepted_at = datetime.utcnow()
+    db.add(order)
+    try:
+        db.commit()
+        db.refresh(order)
+    except SQLAlchemyError as e:
+        db.rollback()
+        raise HTTPException(status_code=500, detail=f"Database error accepting order: {e}")
+    
+    return {"message": "Order accepted successfully"}
+
+@api_router.put("/orders/{order_id}/status")
+async def update_order_status(order_id: str, status: OrderStatus, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
+    # Find order
+    order = db.query(DBOrder).filter(DBOrder.id == order_id).first()
+    if not order:
+        raise HTTPException(status_code=404, detail="Order not found")
+    
+    # Check permissions
+    if current_user.user_type == UserType.DRIVER:
+        if order.driver_id != current_user.id:
+            raise HTTPException(status_code=403, detail="You can only update your own orders")
+    elif current_user.user_type == UserType.CLIENT: # Client can't update order status this way, usually only cancel or view
+        raise HTTPException(status_code=403, detail="Clients cannot directly update order status.")
+    
+    # Update order
+    order.status = status
+    if status == OrderStatus.DELIVERED:
+        order.delivered_at = datetime.utcnow()
+        # For cash payments, payment status is updated by driver via separate endpoint
+        if order.payment_method != PaymentMethod.CASH: # If not cash, assume it's paid (e.g., card)
+            order.payment_status = PaymentStatus.COMPLETED
+        
+        # Update driver earnings
+        if order.financials and order.driver_id:
+            driver_user = db.query(DBUser).filter(DBUser.id == order.driver_id).first()
+            if driver_user:
+                financials_dict = json.loads(order.financials) # Load JSON string
+                driver_user.total_earnings += financials_dict.get("driver_earnings", 0)
+                db.add(driver_user)
+                db.commit()
+                db.refresh(driver_user)
+    
+    db.add(order)
+    try:
+        db.commit()
+        db.refresh(order)
+    except SQLAlchemyError as e:
+        db.rollback()
+        raise HTTPException(status_code=500, detail=f"Database error updating order status: {e}")
+    
+    return {"message": "Order status updated successfully"}
+
+# ADMIN ROUTES
+@api_router.get("/admin/stats", response_model=AdminStats)
+async def get_admin_stats(current_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
+    """Get comprehensive admin statistics"""
+    
+    # Get current month dates
+    now = datetime.utcnow()
+    start_of_month = datetime(now.year, now.month, 1)
+    
+    # Aggregate statistics
+    total_orders = db.query(DBOrder).count()
+    active_users = db.query(DBUser).filter(DBUser.is_active == True, DBUser.user_type != UserType.ADMIN).count()
+    active_drivers = db.query(DBUser).filter(DBUser.is_active == True, DBUser.user_type == UserType.DRIVER).count()
+    pending_orders = db.query(DBOrder).filter(DBOrder.status == OrderStatus.PENDING).count()
+    completed_orders = db.query(DBOrder).filter(DBOrder.status == OrderStatus.DELIVERED).count()
+    
+    # Revenue calculations
+    # Need to sum from financials column which is Text, so retrieve and sum in Python
+    delivered_orders = db.query(DBOrder).filter(DBOrder.status == OrderStatus.DELIVERED, DBOrder.financials.isnot(None)).all()
+    
+    total_revenue = sum(json.loads(order.financials).get("total_amount", 0) for order in delivered_orders)
+    total_commission = sum(json.loads(order.financials).get("owner_earnings", 0) for order in delivered_orders)
+    
+    # Calculate average order value from delivered orders
+    if delivered_orders:
+        total_delivered_amount = sum(json.loads(order.financials).get("total_amount", 0) for order in delivered_orders)
+        avg_order_value = total_delivered_amount / len(delivered_orders)
+    else:
+        avg_order_value = 0.0
+    
+    # Monthly revenue
+    monthly_delivered_orders = db.query(DBOrder).filter(
+        DBOrder.status == OrderStatus.DELIVERED,
+        DBOrder.delivered_at >= start_of_month,
+        DBOrder.financials.isnot(None)
+    ).all()
+    
+    monthly_revenue = sum(json.loads(order.financials).get("total_amount", 0) for order in monthly_delivered_orders)
+    monthly_commission = sum(json.loads(order.financials).get("owner_earnings", 0) for order in monthly_delivered_orders)
+    
+    return AdminStats(
+        total_orders=total_orders,
+        total_revenue=total_revenue,
+        total_commission_earned=total_commission,
+        active_users=active_users,
+        active_drivers=active_drivers,
+        pending_orders=pending_orders,
+        completed_orders=completed_orders,
+        monthly_revenue=monthly_revenue,
+        monthly_commission=monthly_commission,
+        average_order_value=avg_order_value
+    )
+
+# Removed Stripe checkout session endpoints (as per previous request)
+# @api_router.post("/checkout/session", response_model=CheckoutSessionResponse)
+# async def create_checkout_session(checkout_request: CheckoutRequest, current_user: User = Depends(get_current_user)):
+#    ... (removed Stripe logic)
+
+# @api_router.get("/checkout/status/{session_id}", response_model=CheckoutStatusResponse)
+# async def get_checkout_status(session_id: str, current_user: User = Depends(get_current_user)):
+#    ... (removed Stripe logic)
+
+async def create_driver_payout_for_order(order_id: str): # This function needs `db` parameter
+    """Create driver payout when order is paid (for cash, this is handled differently)"""
+    db = SessionLocal() # Get session for internal call
+    try:
+        # Get order details
+        order = db.query(DBOrder).filter(DBOrder.id == order_id).first()
+        if not order or not order.driver_id:
+            return
+
+        # Check if payout already exists
+        existing_payout = db.query(DBDriverPayout).filter(DBDriverPayout.order_id == order_id).first()
+        if existing_payout:
+            return
+
+        # Calculate driver earnings
+        financials = json.loads(order.financials) if order.financials else {}
+        driver_earnings = financials.get("driver_earnings", 0)
+
+        # Create payout record
+        payout = DBDriverPayout(
+            driver_id=order.driver_id,
+            order_id=order_id,
+            amount=driver_earnings,
+            currency="mxn",
+            payment_method=PaymentMethod.CASH, # Explicitly cash
+            transfer_status=TransferStatus.PENDING
+        )
+
+        db.add(payout)
+        db.commit()
+        db.refresh(payout)
+        print(f"✅ Driver payout created for order {order_id}: ${driver_earnings} MXN")
+
+    except SQLAlchemyError as e:
+        db.rollback()
+        print(f"❌ Database error creating driver payout: {e}")
+    except Exception as e:
+        print(f"❌ Error creating driver payout: {e}")
+    finally:
+        db.close() # Close session for internal call
+
+@api_router.post("/payment/cash")
+async def process_cash_payment(cash_request: CashPaymentRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
+    """Process cash payment for an order"""
+    # Get the order
+    order = db.query(DBOrder).filter(DBOrder.id == cash_request.order_id).first()
+    if not order:
+        raise HTTPException(status_code=404, detail="Order not found")
+    
+    # Verify the order belongs to the current user
+    if order.client_id != current_user.id:
+        raise HTTPException(status_code=403, detail="Not authorized to pay for this order")
+    
+    # Check if order is already paid or set for cash
+    if order.payment_status == PaymentStatus.PAID and order.payment_method == PaymentMethod.CASH:
+        raise HTTPException(status_code=400, detail="Order already set for cash payment and paid")
+    if order.payment_method == PaymentMethod.CASH and order.payment_status == PaymentStatus.PENDING:
+        financials_dict = json.loads(order.financials) if order.financials else {}
+        return {"message": "Order already set for cash payment", "total_amount": financials_dict.get("total_amount", 0)}
+
+
+    # Calculate total amount including commissions
+    financials = calculate_order_financials(order.price) # Re-calculate to ensure consistency
+
+    # Update order to cash payment
+    order.payment_status = PaymentStatus.PENDING
+    order.payment_method = PaymentMethod.CASH
+    order.financials = json.dumps(financials.model_dump()) # Store as JSON string
+    db.add(order)
+    try:
+        db.commit()
+        db.refresh(order)
+    except SQLAlchemyError as e:
+        db.rollback()
+        raise HTTPException(status_code=500, detail=f"Database error updating order for cash payment: {e}")
+    
+    # Create payment transaction record
+    payment_transaction = DBPaymentTransaction(
+        user_id=current_user.id,
+        order_id=cash_request.order_id,
+        amount=financials.total_amount,
+        currency="mxn",
+        payment_method=PaymentMethod.CASH,
+        payment_status=PaymentStatus.PENDING,
+        metadata=json.dumps({ # Store metadata as JSON string
+            "base_price": str(financials.subtotal),
+            "commission": str(financials.commission_amount),
+            "service_fee": str(financials.service_fee),
+            "iva_amount": str(financials.iva_amount),
+            "total_amount": str(financials.total_amount)
+        })
+    )
+    
+    db.add(payment_transaction)
+    try:
+        db.commit()
+        db.refresh(payment_transaction)
+    except SQLAlchemyError as e:
+        db.rollback()
+        raise HTTPException(status_code=500, detail=f"Database error creating cash payment transaction: {e}")
+    
+    return {"message": "Order set to cash payment", "total_amount": financials.total_amount}
+
+@api_router.post("/payment/cash/complete/{order_id}")
+async def complete_cash_payment(order_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
+    """Complete cash payment when driver delivers order"""
+    # Get the order
+    order = db.query(DBOrder).filter(DBOrder.id == order_id).first()
+    if not order:
+        raise HTTPException(status_code=404, detail="Order not found")
+    
+    # Verify the current user is the driver for this order
+    if order.driver_id != current_user.id:
+        raise HTTPException(status_code=403, detail="Only the assigned driver can complete cash payment")
+    
+    # Check if order is cash payment and not already completed
+    if order.payment_method != PaymentMethod.CASH:
+        raise HTTPException(status_code=400, detail="Order is not a cash payment")
+    
+    if order.payment_status == PaymentStatus.PAID:
+        raise HTTPException(status_code=400, detail="Payment already completed")
+    
+    # Update order payment status
+    order.payment_status = PaymentStatus.PAID
+    db.add(order)
+    try:
+        db.commit()
+        db.refresh(order)
+    except SQLAlchemyError as e:
+        db.rollback()
+        raise HTTPException(status_code=500, detail=f"Database error updating order payment status: {e}")
+    
+    # Update payment transaction record
+    payment_transaction = db.query(DBPaymentTransaction).filter(
+        DBPaymentTransaction.order_id == order_id, 
+        DBPaymentTransaction.payment_method == PaymentMethod.CASH, 
+        DBPaymentTransaction.payment_status == PaymentStatus.PENDING
+    ).first()
+
+    if payment_transaction:
+        payment_transaction.payment_status = PaymentStatus.PAID
+        payment_transaction.updated_at = datetime.utcnow()
+        db.add(payment_transaction)
+        try:
+            db.commit()
+            db.refresh(payment_transaction)
+        except SQLAlchemyError as e:
+            db.rollback()
+            raise HTTPException(status_code=500, detail=f"Database error updating payment transaction: {e}")
+    
+    # Create cash collection record for commission tracking
+    financials_dict = json.loads(order.financials) if order.financials else {}
+    cash_collection = DBCashCollection(
+        driver_id=current_user.id,
+        order_id=order_id,
+        amount_collected=financials_dict.get("total_amount", 0),
+        commission_owed=financials_dict.get("owner_earnings", 0), # Sum of commission_amount + service_fee + iva_amount
+        currency="mxn",
+        payment_status=PaymentStatus.PENDING  # Driver owes commission to Leonardo (owner)
+    )
+    
+    db.add(cash_collection)
+    try:
+        db.commit()
+        db.refresh(cash_collection)
+    except SQLAlchemyError as e:
+        db.rollback()
+        raise HTTPException(status_code=500, detail=f"Database error creating cash collection record: {e}")
+    
+    # Create driver payout (as driver has collected payment and owner owes driver their share)
+    # Note: create_driver_payout_for_order will get its own session, or can be passed `db`
+    await create_driver_payout_for_order(order_id) # Call the async function
+    
+    return {"message": "Cash payment completed successfully"}
+
+@api_router.get("/admin/driver-payouts", response_model=List[DriverPayout]) # Changed response model
+async def get_driver_payouts(current_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
+    """Get all driver payouts for admin management"""
+    payouts = db.query(DBDriverPayout).all()
+    
+    # Enrich with driver and order details (handled by Pydantic model_validate and SQLAlchemy relationships)
+    # We will need to adjust the UserResponse/OrderResponse to include necessary fields or join
+    # For now, return raw Pydantic models, frontend can fetch details.
+    return [DriverPayout.model_validate(payout) for payout in payouts]
+
+@api_router.get("/admin/cash-collections", response_model=List[DBCashCollection]) # Changed response model
+async def get_cash_collections(current_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
+    """Get all cash collections for admin management"""
+    collections = db.query(DBCashCollection).all()
+    
+    return [DBCashCollection.model_validate(collection) for collection in collections]
+
+@api_router.post("/admin/process-driver-payout/{payout_id}")
+async def process_driver_payout(payout_id: str, current_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
+    """Process payout to driver via bank transfer"""
+    # Get payout record
+    payout = db.query(DBDriverPayout).filter(DBDriverPayout.id == payout_id).first()
+    if not payout:
+        raise HTTPException(status_code=404, detail="Payout not found")
+    
+    if payout.transfer_status != TransferStatus.PENDING:
+        raise HTTPException(status_code=400, detail="Payout already processed")
+    
+    # In a real implementation, this would integrate with a bank transfer API
+    # For now, we'll mark it as completed
+    payout.transfer_status = TransferStatus.COMPLETED
+    payout.updated_at = datetime.utcnow()
+    db.add(payout)
+    try:
+        db.commit()
+        db.refresh(payout)
+    except SQLAlchemyError as e:
+        db.rollback()
+        raise HTTPException(status_code=500, detail=f"Database error processing payout: {e}")
+    
+    return {"message": "Driver payout processed successfully"}
+
+@api_router.post("/admin/mark-commission-paid/{collection_id}")
+async def mark_commission_paid(collection_id: str, current_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
+    """Mark commission as paid by driver"""
+    # Get collection record
+    collection = db.query(DBCashCollection).filter(DBCashCollection.id == collection_id).first()
+    if not collection:
+        raise HTTPException(status_code=404, detail="Collection not found")
+    
+    if collection.payment_status == PaymentStatus.PAID:
+        raise HTTPException(status_code=400, detail="Commission already marked as paid")
+    
+    # Update collection status
+    collection.payment_status = PaymentStatus.PAID
+    db.add(collection)
+    try:
+        db.commit()
+        db.refresh(collection)
+    except SQLAlchemyError as e:
+        db.rollback()
+        raise HTTPException(status_code=500, detail=f"Database error marking commission as paid: {e}")
+    
+    return {"message": "Commission marked as paid successfully"}
+
+# Removed Stripe webhook endpoint (as per previous request)
+# @api_router.post("/webhook/stripe")
+# async def stripe_webhook(request: Request):
+#    ... (removed Stripe webhook logic)
+
+@api_router.get("/payments/transactions", response_model=List[PaymentTransaction]) # Changed response model
+async def get_payment_transactions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
+    """Get payment transactions for the current user"""
+    if current_user.user_type == UserType.ADMIN:
+        # Admin can see all transactions
+        transactions = db.query(DBPaymentTransaction).all()
+    else:
+        # Regular users can only see their own transactions
+        transactions = db.query(DBPaymentTransaction).filter(DBPaymentTransaction.user_id == current_user.id).all()
+    
+    return [PaymentTransaction.model_validate(t) for t in transactions]
+
+@api_router.put("/admin/commission-config")
+async def update_commission_config(config: CommissionConfig, current_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
+    """Update commission configuration"""
+    # Try to find existing config
+    db_config = db.query(DBCommissionConfig).first()
+
+    if db_config:
+        db_config.commission_rate = config.commission_rate
+        db_config.service_fee = config.service_fee
+        db_config.premium_subscription_monthly = config.premium_subscription_monthly
+        db_config.updated_at = datetime.utcnow()
+        db_config.updated_by = current_user.id
+        db.add(db_config)
+    else:
+        # Create new config if none exists
+        new_config = DBCommissionConfig(
+            commission_rate=config.commission_rate,
+            service_fee=config.service_fee,
+            premium_subscription_monthly=config.premium_subscription_monthly,
+            updated_by=current_user.id
+        )
+        db.add(new_config)
+    
+    try:
+        db.commit()
+        if not db_config: db.refresh(new_config)
+    except SQLAlchemyError as e:
+        db.rollback()
+        raise HTTPException(status_code=500, detail=f"Database error updating commission config: {e}")
+    
+    return {"message": "Commission configuration updated successfully"}
+
+@api_router.get("/admin/commission-config", response_model=CommissionConfig)
+async def get_commission_config(current_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
+    """Get current commission configuration"""
+    config = db.query(DBCommissionConfig).first()
+    if not config:
+        # Return default configuration if not found in DB
+        return CommissionConfig(
+            commission_rate=settings.DEFAULT_COMMISSION_RATE,
+            service_fee=settings.SERVICE_FEE,
+            premium_subscription_monthly=settings.PREMIUM_SUBSCRIPTION_MONTHLY
+        )
+    return CommissionConfig.model_validate(config)
+
+@api_router.put("/admin/users/{user_id}/toggle-status")
+async def toggle_user_status(user_id: str, current_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
+    """Toggle user active/inactive status"""
+    # Get user
+    user = db.query(DBUser).filter(DBUser.id == user_id).first()
+    if not user:
+        raise HTTPException(status_code=404, detail="User not found")
+    
+    # Toggle active status
+    new_status = not user.is_active
+    
+    # Update user
+    user.is_active = new_status
+    user.updated_at = datetime.utcnow()
+    db.add(user)
+    try:
+        db.commit()
+        db.refresh(user)
+    except SQLAlchemyError as e:
+        db.rollback()
+        raise HTTPException(status_code=500, detail=f"Database error toggling user status: {e}")
+    
+    action = "activated" if new_status else "deactivated"
+    return {"message": f"User {action} successfully", "is_active": new_status}
+
+@api_router.get("/admin/users", response_model=List[UserResponse])
+async def get_all_users(current_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
+    """Get all users for admin management"""
+    users = db.query(DBUser).filter(DBUser.user_type != UserType.ADMIN).all()
+    return [UserResponse.model_validate(user) for user in users]
+
+
+# Stripe Integration (Removed as per previous user request)
+# @api_router.post("/payments/create-intent")
+# async def create_payment_intent(order_id: str, current_user: User = Depends(get_current_user)):
+#    ... (removed Stripe payment intent creation)
+
+@api_router.post("/verification/send-email")
+async def send_email_verification_code(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
+    """Send email verification code to driver"""
+    if current_user.user_type != UserType.DRIVER:
+        raise HTTPException(status_code=403, detail="Only drivers can verify email")
+    
+    # Generate verification code
+    verification_code = generate_verification_code()
+    
+    # Create email verification record (or update existing pending one)
+    existing_verification = db.query(DBEmailVerification).filter(
+        DBEmailVerification.user_id == current_user.id,
+        DBEmailVerification.status == VerificationStatus.PENDING
+    ).first()
+
+    if existing_verification:
+        # Update existing record
+        existing_verification.verification_code = verification_code
+        existing_verification.created_at = datetime.utcnow()
+        existing_verification.expires_at = datetime.utcnow() + timedelta(hours=24)
+        existing_verification.attempts = 0
+        existing_verification.status = VerificationStatus.PENDING
+        db.add(existing_verification)
+    else:
+        # Create new record
+        new_verification = DBEmailVerification(
+            user_id=current_user.id,
+            email=current_user.email,
+            verification_code=verification_code,
+            expires_at=datetime.utcnow() + timedelta(hours=24)
+        )
+        db.add(new_verification)
+    
+    try:
+        db.commit()
+        if existing_verification: db.refresh(existing_verification)
+        else: db.refresh(new_verification)
+    except SQLAlchemyError as e:
+        db.rollback()
+        raise HTTPException(status_code=500, detail=f"Database error saving verification code: {e}")
+    
+    # Send email (mock)
+    success = await send_email_verification(current_user.email, verification_code, current_user.name)
+    
+    if not success:
+        raise HTTPException(status_code=500, detail="Failed to send verification email (mock)")
+    
+    return {"message": "Verification code sent to email", "expires_in": "24 hours"}
+
+@api_router.post("/verification/verify-email")
+async def verify_email_code(request: EmailVerificationRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
+    """Verify email with provided code"""
+    if current_user.user_type != UserType.DRIVER:
+        raise HTTPException(status_code=403, detail="Only drivers can verify email")
+    
+    # Find verification record
+    verification_record = db.query(DBEmailVerification).filter(
+        DBEmailVerification.user_id == current_user.id,
+        DBEmailVerification.status == VerificationStatus.PENDING
+    ).first()
+    
+    if not verification_record:
+        raise HTTPException(status_code=404, detail="No pending verification found.")
+    
+    # Check expiration
+    if datetime.utcnow() > verification_record.expires_at:
+        verification_record.status = VerificationStatus.EXPIRED
+        db.add(verification_record)
+        db.commit()
+        db.refresh(verification_record)
+        raise HTTPException(status_code=400, detail="Verification code expired.")
+    
+    # Check attempts
+    if verification_record.attempts >= verification_record.max_attempts:
+        verification_record.status = VerificationStatus.FAILED
+        db.add(verification_record)
+        db.commit()
+        db.refresh(verification_record)
+        raise HTTPException(status_code=400, detail="Maximum attempts exceeded for verification code.")
+    
+    # Verify code
+    if verification_record.verification_code != request.verification_code:
+        verification_record.attempts += 1
+        db.add(verification_record)
+        db.commit()
+        db.refresh(verification_record)
+        raise HTTPException(status_code=400, detail="Invalid verification code.")
+    
+    # Mark as verified
+    verification_record.status = VerificationStatus.VERIFIED
+    verification_record.verified_at = datetime.utcnow()
+    db.add(verification_record)
+    db.commit()
+    db.refresh(verification_record)
+    
+    # Update user's email_verified status
+    user = db.query(DBUser).filter(DBUser.id == current_user.id).first()
+    if user:
+        user.is_email_verified = True
+        user.updated_at = datetime.utcnow()
+        db.add(user)
+        db.commit()
+        db.refresh(user)
+    
+    return {"message": "Email verified successfully"}
+
+@api_router.post("/verification/upload-document")
+async def upload_driver_document(request: DocumentUploadRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
+    """Upload driver document for verification"""
+    if current_user.user_type != UserType.DRIVER:
+        raise HTTPException(status_code=403, detail="Only drivers can upload documents.")
+    
+    # Check if user is verified
+    if not current_user.is_phone_verified or not current_user.is_email_verified:
+        raise HTTPException(status_code=400, detail="Please verify phone and email first.")
+    
+    # Check if document already exists
+    existing_doc = db.query(DBDocument).filter(DBDocument.user_id == current_user.id, DBDocument.document_type == request.document_type).first()
+    
+    if existing_doc and existing_doc.status == DocumentStatus.APPROVED:
+        raise HTTPException(status_code=400, detail="Document already approved.")
+    
+    # Validate document automatically (mock logic)
+    validation_result = await validate_document_automatically(request.document_type, request.file_data)
+    
+    # Create or update document record
+    if existing_doc:
+        existing_doc.file_name = request.file_name
+        existing_doc.file_data = request.file_data
+        existing_doc.upload_date = datetime.utcnow()
+        existing_doc.status = DocumentStatus.APPROVED if validation_result["is_valid"] else DocumentStatus.REJECTED
+        existing_doc.auto_verified = True
+        existing_doc.verification_confidence = validation_result["confidence"]
+        db.add(existing_doc)
+    else:
+        new_document = DBDocument(
+            user_id=current_user.id,
+            document_type=request.document_type,
+            file_name=request.file_name,
+            file_data=request.file_data,
+            status=DocumentStatus.APPROVED if validation_result["is_valid"] else DocumentStatus.REJECTED,
+            auto_verified=True,
+            verification_confidence=validation_result["confidence"]
+        )
+        db.add(new_document)
+    
+    try:
+        db.commit()
+        if not existing_doc: db.refresh(new_document)
+    except SQLAlchemyError as e:
+        db.rollback()
+        raise HTTPException(status_code=500, detail=f"Database error saving document: {e}")
+    
+    # Check if user has uploaded both required documents (INE and DRIVERS_LICENSE)
+    user_documents = db.query(DBDocument).filter(DBDocument.user_id == current_user.id).all()
+    document_types_uploaded = {doc.document_type for doc in user_documents}
+
+    if DocumentType.INE in document_types_uploaded and DocumentType.DRIVERS_LICENSE in document_types_uploaded:
+        # Mark user as having uploaded documents
+        current_user.documents_uploaded = True
+        current_user.updated_at = datetime.utcnow()
+        db.add(current_user)
+        try:
+            db.commit()
+            db.refresh(current_user)
+        except SQLAlchemyError as e:
+            db.rollback()
+            raise HTTPException(status_code=500, detail=f"Database error updating user document status: {e}")
+    
+    return {"message": "Document uploaded successfully", "document_status": document.status if existing_doc else new_document.status}
+
+@api_router.get("/verification/status", response_model=DriverVerificationStatus) # Added response model
+async def get_driver_verification_status(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
+    """Get driver verification status"""
+    if current_user.user_type != UserType.DRIVER:
+        raise HTTPException(status_code=403, detail="Only drivers can check verification status.")
+    
+    status = check_driver_verification_status(current_user.id, db) # Pass db session
+    if not status:
+        raise HTTPException(status_code=404, detail="User not found or verification status could not be determined.")
+    
+    return status
+
+@api_router.get("/verification/documents", response_model=List[DBDocument]) # Changed response model
+async def get_driver_documents(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
+    """Get driver uploaded documents"""
+    if current_user.user_type != UserType.DRIVER:
+        raise HTTPException(status_code=403, detail="Only drivers can view documents.")
+    
+    documents = db.query(DBDocument).filter(DBDocument.user_id == current_user.id).all()
+    
+    return documents
+
+@api_router.get("/admin/drivers/verification", response_model=List[dict])
+async def get_all_drivers_verification_status(current_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
+    """Get verification status for all drivers"""
+    # Get all drivers
+    drivers = db.query(DBUser).filter(DBUser.user_type == UserType.DRIVER).all()
+    
+    verification_statuses = []
+    for driver in drivers:
+        status = check_driver_verification_status(driver.id, db) # Pass db session
+        if status:
+            verification_statuses.append({
+                "driver_id": driver.id,
+                "driver_name": driver.name,
+                "driver_email": driver.email,
+                "verification_status": status.model_dump() # Convert Pydantic model to dict
+            })
+    
+    return {"drivers": verification_statuses}
+
+@api_router.post("/admin/drivers/{driver_id}/approve")
+async def approve_driver_verification(driver_id: str, current_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
+    """Manually approve driver verification"""
+    driver = db.query(DBUser).filter(DBUser.id == driver_id, DBUser.user_type == UserType.DRIVER).first()
+    if not driver:
+        raise HTTPException(status_code=404, detail="Driver not found.")
+    
+    # Update driver status
+    driver.status = UserStatus.APPROVED
+    driver.admin_approved = True
+    driver.updated_at = datetime.utcnow()
+    db.add(driver)
+    try:
+        db.commit()
+        db.refresh(driver)
+    except SQLAlchemyError as e:
+        db.rollback()
+        raise HTTPException(status_code=500, detail=f"Database error approving driver: {e}")
+    
+    return {"message": "Driver approved successfully."}
+
+@api_router.post("/admin/drivers/{driver_id}/reject")
+async def reject_driver_verification(driver_id: str, current_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
+    """Manually reject driver verification"""
+    driver = db.query(DBUser).filter(DBUser.id == driver_id, DBUser.user_type == UserType.DRIVER).first()
+    if not driver:
+        raise HTTPException(status_code=404, detail="Driver not found.")
+    
+    # Update driver status
+    driver.status = UserStatus.REJECTED
+    driver.admin_approved = False
+    driver.updated_at = datetime.utcnow()
+    db.add(driver)
+    try:
+        db.commit()
+        db.refresh(driver)
+    except SQLAlchemyError as e:
+        db.rollback()
+        raise HTTPException(status_code=500, detail=f"Database error rejecting driver: {e}")
+    
+    return {"message": "Driver rejected successfully."}
+
+# Removed Stripe Integration endpoints (as per previous request)
+# @api_router.post("/payments/create-intent")
+# async def create_payment_intent(order_id: str, current_user: User = Depends(get_current_user)):
+#    ... (removed Stripe payment intent creation)
+
+# Include the router in the main app
+app.include_router(api_router)
+
+@app.on_event("startup")
+async def startup_event():
+    """Initialize application on startup"""
+    # Create tables
+    Base.metadata.create_all(bind=engine)
+    # Initialize owner (this will insert if not exists)
+    await initialize_owner()
+    logger.info("🚀 RapidMandados API started successfully - México")
+    logger.info(f"👑 Owner: {settings.OWNER_NAME} ({settings.OWNER_EMAIL})")
+    logger.info(f"💰 Commission Rate: {settings.DEFAULT_COMMISSION_RATE*100}%")
+    logger.info(f"💳 Service Fee: ${settings.SERVICE_FEE} {CURRENCY}")
+    logger.info(f"🇲🇽 Currency: {CURRENCY} - {COUNTRY}")
+
+
+# No client.close() needed for SQLAlchemy engine in this setup, sessions are closed via dependency.