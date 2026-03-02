# AutoDW ⚡
Automated Star Schema Data Warehouse Builder

AutoDW transforms messy CSV files into a production-ready star schema data warehouse automatically. No manual mapping. No complex ETL scripts. Just upload and analyze.

## ✨ Features
- ⚡ **Auto-Detection** – Intelligently identifies dimensions and facts from raw CSV files  
- 📊 **Star Schema Generation** – Creates 15+ dimension tables with proper surrogate keys  
- 🔗 **Smart Relationships** – Automatically builds foreign key connections between facts and dimensions  
- 🐳 **Docker Ready** – One-command local deployment with containerized architecture  
- ☁️ **Cloud Ready** – Live deployment possible on AWS EC2  
- 📈 **Scalable** – Processes 115K+ rows in seconds  

---

## 🚀 Quick Start

### 1️⃣ Local Deployment with Docker
```bash
# Clone the repository
git clone https://github.com/sanjayvinayak2711/autodw.git
cd autodw

# Run the application
docker-compose up -d

# Access the dashboard locally
open http://localhost:5000


2️⃣ Cloud Deployment on AWS EC2
# Launch an EC2 instance with Docker installed

# Clone the repository on EC2
git clone https://github.com/sanjayvinayak2711/autodw.git
cd autodw

# Start the application
docker-compose up -d

# Access the dashboard from your browser
http://<EC2-PUBLIC-IP>:5000
