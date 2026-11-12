# Come and Stay Hotel - Chatbot

A sophisticated hotel booking chatbot built with Rasa Framework that enables users to search hotels, make reservations, check booking status, and cancel bookings through natural conversation.

## 🏨 Features

- **Hotel Search**: Find available hotels by city and dates
- **Booking Management**: Create, view, and cancel hotel reservations
- **Natural Language Processing**: Understands conversational user inputs
- **Database Integration**: MySQL backend for persistent booking storage
- **Web Interface**: Modern, responsive chat UI
- **Email Notifications**: Booking confirmations via email

## 📋 Prerequisites

- Python 3.8 or higher
- MySQL Server 8.0 or higher
- Git
- Virtual environment (recommended)

## 🛠️ Installation & Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd HotelBot_Basemodel
```

### 2. Create Virtual Environment
```bash
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Setup

#### Install MySQL (if not already installed)
```bash
# macOS
brew install mysql
brew services start mysql

# Ubuntu/Debian
sudo apt update
sudo apt install mysql-server
sudo systemctl start mysql
```

#### Create Database and User
```sql
mysql -u root -p
CREATE DATABASE hotelbot;
CREATE USER 'user_name'@'localhost' IDENTIFIED BY '*********';
GRANT ALL PRIVILEGES ON hotelbot.* TO 'user_name'@'localhost';
FLUSH PRIVILEGES;
```

#### Create Bookings Table
```sql
USE hotelbot;
CREATE TABLE bookings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id VARCHAR(20) UNIQUE NOT NULL,
    guests VARCHAR(10) NOT NULL,
    email VARCHAR(100) NOT NULL,
    checkin DATE NOT NULL,
    checkout DATE NOT NULL,
    city VARCHAR(50) NOT NULL,
    hotel VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 5. Train the Rasa Model
```bash
rasa train
```

## 🚀 Running the Application

### Step 1: Start Action Server
Open **Terminal 1**:
```bash
source env/bin/activate
rasa run actions
```
Expected output:
```
Action endpoint is up and running on http://0.0.0.0:5055
```

### Step 2: Start Rasa Core Server
Open **Terminal 2**:
```bash
source env/bin/activate
rasa run --enable-api --cors "*"
```
Expected output:
```
Starting Rasa server on http://0.0.0.0:5005
```

### Step 3: Launch Web Interface
Open the chat interface in your browser:
```bash
open index.html
```
Or navigate to: `file:///path/to/HotelBot_Basemodel/index.html`

## 💬 Usage Examples

### Hotel Search
- "Find hotels in New York for 2 guests from 23-11-2025 to 25-11-2025"
- "I need a hotel in Munich for this weekend"
- "Show me available hotels in London"

### Booking Management
- "Book Hotel Berlin City for 2 guests from 23-11-2025 to 25-11-2025"
- "Check my booking status for HTL-12345"
- "Cancel my booking HTL-12345"

### General Queries
- "Hi" / "Hello" - Greeting
- "What hotels do you have?"
- "Help me with booking"

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Browser   │    │  Rasa Core       │    │  Action Server  │
│   (index.html)  │◄──►│  (Port 5005)     │◄──►│  (Port 5055)    │
│                 │    │                  │    │                 │
│ • Chat UI       │    │ • NLU Processing │    │ • Hotel Search  │
│ • User Input    │    │ • Dialogue Mgmt  │    │ • Booking Logic │
│ • Bot Responses │    │ • API Endpoints  │    │ • DB Operations │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │   MySQL DB      │
                                              │  (hotelbot)     │
                                              │                 │
                                              │ • Bookings      │
                                              │ • User Data     │
                                              │ • Hotel Info    │
                                              └─────────────────┘
```

## 🔧 Configuration

### Environment Variables
```bash
# Database Configuration
export HOTELBOT_DB_HOST="localhost"
export HOTELBOT_DB_PORT="3306"
export HOTELBOT_DB_USER="root"
export HOTELBOT_DB_PASSWORD="Ankith@2001"
export HOTELBOT_DB_NAME="hotelbot"
```

### Key Files
- `config.yml` - Rasa model configuration
- `domain.yml` - Bot domain and responses
- `endpoints.yml` - Action server endpoints
- `actions/actions.py` - Custom action implementations
- `data/` - Training data (NLU, stories, rules)

## 🔒 Security & Data Storage

### User Information Storage
- **Database**: MySQL with encrypted connections
- **Data Collected**: Email, booking dates, guest count, city, hotel preferences
- **Security Measures**: Password authentication, input validation, SQL injection prevention

### Storage Rules & Compliance
- **GDPR Compliance**: User consent for data collection
- **Data Minimization**: Store only essential booking information
- **Retention Policy**: Booking data retained for 7 years
- **Right to Deletion**: Users can cancel bookings anytime
- **Access Control**: Role-based permissions for database access

## 🐛 Troubleshooting

### Common Issues

#### 1. "Could not reach bot" Error
**Solution**: Ensure both servers are running:
- Check action server on port 5055
- Check Rasa core server on port 5005

#### 2. Database Connection Error
**Solution**: Verify MySQL credentials:
```bash
mysql -u root -p"Ankith@2001" -e "SELECT 1"
```

#### 3. Port Already in Use
**Solution**: Kill existing processes:
```bash
lsof -ti:5005 | xargs kill -9
lsof -ti:5055 | xargs kill -9
```

#### 4. Model Training Issues
**Solution**: Check training data format:
```bash
rasa data validate
```

### Debug Mode
Enable debug logging:
```bash
rasa run actions --debug
rasa run --debug
```

## 📊 API Endpoints

### Rasa Core API
- **POST** `/webhooks/rest/webhook` - Send messages to bot
- **GET** `/status` - Check server status

### Action Server API
- **POST** `/webhook` - Execute custom actions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For support and questions:
- Check the troubleshooting section
- Review Rasa documentation: https://rasa.com/docs/
- Create an issue in the repository

## 🔄 Version History

- **v1.0.0** - Initial release with basic hotel booking functionality
- **v1.1.0** - Added database integration and booking management
- **v1.2.0** - Enhanced UI and error handling

---

**Note**: This chatbot is designed for demonstration purposes. For production use, additional security measures, scalability considerations, and compliance audits are recommended.
