import csv
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE1_URL"))
db = scoped_session(sessionmaker(bind=engine))
def main():
    f = open("books.csv")
    reader = csv.reader(f)
    for isbn,title, author, year in reader:
        db.execute("INSERT INTO books (_isbn, _title, author, year) VALUES (:_isbn, :_title, :author, :year)",{"_isbn": isbn, "_title": title, "author":author, "year":year}) 
    db.commit()
if __name__ == "__main__":
    main()