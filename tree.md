# Tsukishima Tree Structure
```markdown
tsukishima/
├── .gitignore
├── LICENSE
├── README.md
├── docker-compose.yml
├── tree.md
├── app/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py              # FastAPI main logic
│   ├── database.py          # DB connection & session management
│   ├── models.py            # SQLAlchemy ORM models
│   ├── schemas.py           # Pydantic validation schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── face_service.py  # DeepFace image processing logic
│   │   └── search_service.py# Vector/Database search logic
│   └── scripts/
│       ├── register_faces.py# Bulk face registration script
│       └── images/          # Seed image files for local registration
│           ├── 224999_Genius_Railway.jpg
│           └── ...
└── db/
    └── init.sql             # Database initialization script
```