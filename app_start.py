import json
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel

from typing import List, Optional
from sqlalchemy import ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Text
from langchain_ollama.llms import OllamaLLM
from dotenv import load_dotenv
import os

load_dotenv()

engine = create_engine(os.environ.get("DATABASE_URL"))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency to get DB session


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI(
    title="Book Review API",
    description="API for managing books and reviews with LLM integration for summaries and recommendations.",
    version="1.0.0"
)


class Book(BaseModel):
    id: Optional[int] = None
    title: str
    author: str
    genre: Optional[str] = ""
    year_published: Optional[int] = ""
    summary: Optional[str] = ""

    class Config:
        orm_mode = True


class Review(BaseModel):
    id: Optional[int] = None
    book_id: Optional[int] = None
    user_id: int
    review_text: str
    rating: int

    class Config:
        orm_mode = True


class Summary(BaseModel):
    summary: str
    rating: float


class BookModel(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String, index=True)
    author = Column(String, index=True)
    genre = Column(String, index=True)
    year_published = Column(Integer, index=True)
    summary = Column(Text, index=True)


class ReviewModel(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey('books.id'), nullable=False)
    user_id = Column(Integer, index=True)
    review_text = Column(Text, index=True)
    rating = Column(Integer, index=True)


@app.on_event("startup")
async def startup_event():
    # Check PostgreSQL connection
    try:
        with engine.connect() as connection:
            connection.execute("SELECT 1")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="PostgreSQL is not accessible")

    # Check Ollama LLM model accessibility
    try:
        model = OllamaLLM(model="llama3")
        model.invoke("Test connection")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Ollama LLM model is not accessible")


@app.post("/books", response_model=Book, summary="Add a new book", description="Add a new book to the database.")
async def add_book(book: Book, db: Session = Depends(get_db)):
    Base.metadata.create_all(bind=engine)
    db_book = BookModel(
        title=book.title,
        author=book.author,
        genre=book.genre,
        year_published=book.year_published,
        summary=book.summary
    )
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book


@app.get("/books", response_model=List[Book], summary="Get all books", description="Retrieve a list of all books.")
async def get_books(db: Session = Depends(get_db)):
    books = db.query(BookModel).all()
    return books


@app.get("/books/{id}", response_model=Book, summary="Get a book by ID", description="Retrieve a book by its ID.")
async def get_book(id: int, db: Session = Depends(get_db)):
    book = db.query(BookModel).filter(BookModel.id == id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@app.put("/books/{id}", response_model=Book, summary="Update a book", description="Update the details of a book by its ID.")
async def update_book(id: int, book: Book, db: Session = Depends(get_db)):
    db_book = db.query(BookModel).filter(BookModel.id == id).first()
    if not db_book:
        raise HTTPException(status_code=404, detail="Book not found")

    db_book.title = book.title
    db_book.author = book.author
    db_book.genre = book.genre
    db_book.year_published = book.year_published
    db_book.summary = book.summary

    db.commit()
    db.refresh(db_book)
    return db_book


@app.delete("/books/{id}", summary="Delete a book", description="Delete a book by its ID.")
async def delete_book(id: int, db: Session = Depends(get_db)):
    book = db.query(BookModel).filter(BookModel.id == id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    db.delete(book)
    db.commit()
    return {"detail": "Book deleted successfully"}


@app.post("/books/{id}/reviews", response_model=Review, summary="Add a review", description="Add a review for a specific book.")
async def add_review(id: int, review: Review, db: Session = Depends(get_db)):
    book = db.query(BookModel).filter(BookModel.id == id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    db_review = ReviewModel(
        book_id=book.id,
        user_id=review.user_id,
        review_text=review.review_text,
        rating=review.rating
    )

    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review


@app.get("/books/{id}/reviews", response_model=List[Review], summary="Get reviews for a book", description="Retrieve all reviews for a specific book.")
async def get_reviews(id: int, db: Session = Depends(get_db)):
    reviews = db.query(ReviewModel).filter(ReviewModel.book_id == id).all()
    if not reviews:
        raise HTTPException(
            status_code=404, detail="No reviews found for this book")
    return reviews


@app.get("/books/{id}/summary", response_model=Summary, summary="Get book summary", description="Generate a summary for a specific book based on its reviews.")
async def get_summary(id: int, db: Session = Depends(get_db)):
    book = db.query(BookModel).filter(BookModel.id == id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    reviews = db.query(ReviewModel).filter(ReviewModel.book_id == id).all()
    if not reviews:
        raise HTTPException(
            status_code=404, detail="No reviews found for this book")

    summary_texts = [review.review_text for review in reviews]
    average_rating = sum(review.rating for review in reviews) / len(reviews)
    model = OllamaLLM(model="llama3")
    response = model.invoke("Summarize the following reviews: " +
                            " ".join(summary_texts))
    return {"summary": response, "rating": average_rating}


@app.get("/recommendations", response_model=List[Book], summary="Get book recommendations", description="Get book recommendations based on user preferences.")
async def get_recommendations(db: Session = Depends(get_db)):
    user_preferences = ["fiction", "adventure",
                        "mystery"]  # Example user preferences

    books = db.query(BookModel).all()
    if not books:
        raise HTTPException(status_code=404, detail="No books found")

    book_summaries = [book.summary for book in books]
    book_titles = [book.title for book in books]
    model = OllamaLLM(model="llama3")
    response = model.invoke(
        f"Based on the following user preferences: {', '.join(user_preferences)}, recommend books from the following list: {', '.join(book_titles)} with summaries: {', '.join(book_summaries)}")

    recommended_books = db.query(BookModel).filter(
        BookModel.title.in_(response)).all()
    return recommended_books


@app.post("/generate-summary", response_model=Summary, summary="Generate summary", description="Generate a summary for the provided content.")
async def generate_summary(content: str):
    model = OllamaLLM(model="llama3")
    response = model.invoke(f"Summarize the following content: {content}")
    summary = response.choices[0].text.strip()
    # Assuming no rating is provided for this endpoint
    return Summary(summary=summary, rating=0.0)
