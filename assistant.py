# Enhanced Susan Virtual Assistant - Sports Schedulers Knowledge Base
# Sports Schedulers Web Application  
# Author: Jose Ortiz
# Copyright: 2025

from flask import Blueprint, request, jsonify, session
from utils.decorators import require_login
from utils.logger import log_activity
import re
import json
import random
from datetime import datetime, timedelta

assistant_bp = Blueprint('assistant', __name__, url_prefix='/api/assistant')

class SusanSportsSchedulersAssistant:
    """
    Enhanced Susan Virtual Assistant with Real Sports Schedulers Knowledge
    Contains actual step-by-step procedures for the Sports Schedulers application
    """
    
    def __init__(self):
        self.name = "Susan"
        self.version = "3.0"
        self.personality = {
            "friendly": True,
            "helpful": True,
            "professional": True,
            "encouraging": True,
            "enthusiastic": True
        }
        
        # Conversation context and memory
        self.conversation_memory = {}
        self.user_preferences = {}
        
        # Real Sports Schedulers knowledge base
        self.knowledge_base = self._load_sports_schedulers_knowledge()
        self.conversation_patterns = self._setup_conversation_patterns()
        self.intent_patterns = self._setup_intent_patterns()
        self.emotional_responses = self._load_emotional_responses()
        
    def _load_sports_schedulers_knowledge(self):
        """Load real Sports Schedulers application knowledge"""
        return {
            "greetings": {
                "first_time": [
                    "👋 Hello! I'm Susan, your Sports Schedulers virtual assistant! I know all about how to use this application and I'm here to help you succeed. What would you like to learn?",
                    "Hi there! Welcome to Sports Schedulers! I'm Susan and I can walk you through any feature step-by-step. How can I help you today?",
                    "Hey! 🌟 I'm Susan, your personal guide to Sports Schedulers. I love helping people master this system! What can I show you?"
                ],
                "returning": [
                    "Hey there! Great to see you back! 😊 How's your Sports Schedulers experience going? Need help with anything?",
                    "Welcome back! I was hoping you'd stop by! 🎉 Ready to learn more about Sports Schedulers?",
                    "Hi again! So nice to see a familiar face! How can I help you with Sports Schedulers today?"
                ],
                "time_based": {
                    "morning": [
                        "Good morning! ☀️ Ready to tackle some Sports Schedulers tasks today?",
                        "Morning! Hope you're having a great start! What Sports Schedulers feature can I help you with? ☕"
                    ],
                    "afternoon": [
                        "Good afternoon! How's your scheduling going today? 🌤️",
                        "Afternoon! Need any help navigating Sports Schedulers?"
                    ],
                    "evening": [
                        "Good evening! Still working on scheduling? I'm here to help! 🌙",
                        "Evening! How was your day with Sports Schedulers? Need any assistance?"
                    ]
                }
            },
            
            "casual_conversation": {
                "how_are_you": [
                    "I'm doing wonderful! 😊 I love helping people master Sports Schedulers - it's such a powerful system when you know how to use it! How about you? How's your experience with the app been?",
                    "I'm fantastic! I get excited every time someone asks for help because I get to share all the cool features of Sports Schedulers! What about you - enjoying the application?",
                    "Doing great! I've been helping users all day and it never gets old. Sports Schedulers has so many useful features! How are you finding it?"
                ],
                "compliments": [
                    "Aww, you're so sweet! Thank you! 💕 You know what? You're making great progress learning Sports Schedulers!",
                    "That's so kind! 🥰 You're doing awesome with Sports Schedulers too - keep up the great work!",
                    "You're making me blush! 😊 I love users like you who are eager to learn the system properly!"
                ],
                "jokes_fun": [
                    "Why don't sports schedulers ever get stressed? Because they always have a game plan! 😄 Want to hear how to plan your games in Sports Schedulers?",
                    "What's a scheduler's favorite type of music? Algo-rhythms! 🎵😂 Speaking of rhythm, want me to show you the workflow for adding games?",
                    "Why did the official love Sports Schedulers? Because it made their life so much easier! 🏆😆 Want to see how easy it is to manage assignments?"
                ]
            },
            
            # REAL SPORTS SCHEDULERS PROCEDURES
            "games_management": {
                "add_single_game": {
                    "title": "How to Add a Single Game",
                    "steps": [
                        "1. 📍 Navigate to the **Games** tab in the left sidebar",
                        "2. 🔵 Click the **'Add Game'** button (blue button on the right)",
                        "3. 📝 Fill in the game details:",
                        "   • **Date**: Select the game date",
                        "   • **Time**: Enter the start time",
                        "   • **Home Team**: Enter the home team name",
                        "   • **Away Team**: Enter the visiting team name",
                        "   • **Location**: Choose from existing locations or add new",
                        "   • **Sport**: Select the sport type",
                        "   • **League**: Choose the appropriate league",
                        "   • **Level**: Select the competition level",
                        "   • **Officials Needed**: Set how many officials required",
                        "4. 💾 Click **'Save'** to create the game",
                        "5. ✅ The game will appear in your games list immediately"
                    ],
                    "tips": [
                        "💡 Make sure to select the correct league - this affects which officials can be assigned",
                        "⏰ Double-check the time format (12-hour or 24-hour based on your settings)",
                        "📍 If your location isn't listed, you can add it from the Locations tab first"
                    ]
                },
                "csv_import": {
                    "title": "How to Import Games via CSV",
                    "steps": [
                        "1. 📊 Go to the **Games** tab",
                        "2. 📥 Click **'CSV Template'** to download the template file",
                        "3. 📝 Open the template in Excel or Google Sheets",
                        "4. ✏️ Fill in your game data following the template format:",
                        "   • One game per row",
                        "   • Use exact sport names (Basketball, Football, Soccer, etc.)",
                        "   • Date format: YYYY-MM-DD",
                        "   • Time format: HH:MM (24-hour)",
                        "5. 💾 Save as CSV file",
                        "6. ⬆️ Click **'Import CSV'** button",
                        "7. 📁 Select your CSV file",
                        "8. ✅ Review the preview and click **'Import'**",
                        "9. 🎉 All games will be added to your schedule"
                    ],
                    "tips": [
                        "🔍 Always download the latest template - format may change",
                        "✅ Validate your data before importing - check for typos in team names",
                        "📅 Make sure dates are in the future",
                        "⚠️ Don't leave required fields empty"
                    ]
                },
                "edit_game": {
                    "title": "How to Edit an Existing Game",
                    "steps": [
                        "1. 🎯 Go to **Games** tab",
                        "2. 🔍 Find the game you want to edit",
                        "3. ✏️ Click the **'Edit'** button (pencil icon) for that game",
                        "4. 📝 Modify any details you need to change",
                        "5. 💾 Click **'Save Changes'**",
                        "6. ✅ The game information will be updated"
                    ],
                    "important": "⚠️ If officials are already assigned, they'll be notified of changes automatically"
                }
            },
            
            "officials_management": {
                "add_official": {
                    "title": "How to Add a New Official",
                    "steps": [
                        "1. 👥 Navigate to the **Officials** tab",
                        "2. ➕ Click **'Add Official'** button",
                        "3. 📋 Fill in the official's information:",
                        "   • **Name**: Full name of the official",
                        "   • **Email**: Contact email address",
                        "   • **Phone**: Phone number",
                        "   • **Sports**: Select which sports they can officiate",
                        "   • **Experience Level**: Beginner, Intermediate, Advanced, Expert",
                        "   • **Certifications**: List any certifications",
                        "   • **Travel Radius**: How far they'll travel (in miles)",
                        "4. 💾 Click **'Save Official'**",
                        "5. ✅ The official is now in your system and available for assignments"
                    ],
                    "tips": [
                        "📧 Make sure email is correct - they'll receive assignment notifications",
                        "🏆 Keep certifications up to date for compliance",
                        "📍 Set realistic travel radius for better assignments"
                    ]
                },
                "assign_official": {
                    "title": "How to Assign Officials to Games",
                    "steps": [
                        "1. 📋 Go to **Assignments** tab OR click 'Assign' on a specific game",
                        "2. 🎯 Select the game you want to assign officials to",
                        "3. 👥 View available officials for that game",
                        "4. ✅ Click **'Assign'** next to the official's name",
                        "5. 🎭 Choose their position/role if multiple positions available",
                        "6. 💾 Click **'Confirm Assignment'**",
                        "7. 📧 The official will automatically receive an email notification",
                        "8. ⏳ They can accept or decline the assignment"
                    ],
                    "smart_features": [
                        "🤖 System shows only qualified officials for each sport",
                        "📍 Officials outside travel radius are marked",
                        "⚠️ Conflicts with other assignments are highlighted",
                        "⭐ Higher-rated officials appear first"
                    ]
                }
            },
            
            "assignments_workflow": {
                "view_assignments": {
                    "title": "How to View and Manage Assignments",
                    "steps": [
                        "1. 📋 Click **Assignments** tab in sidebar",
                        "2. 📊 View all assignments with status indicators:",
                        "   • 🟡 **Pending**: Waiting for official response",
                        "   • 🟢 **Accepted**: Official confirmed",
                        "   • 🔴 **Declined**: Official declined",
                        "   • ⚫ **Unassigned**: No official assigned yet",
                        "3. 🔍 Use filters to narrow down view:",
                        "   • By date range",
                        "   • By sport",
                        "   • By status",
                        "   • By official",
                        "4. 📱 Click any assignment for detailed view"
                    ]
                },
                "handle_declined": {
                    "title": "What to Do When Official Declines",
                    "steps": [
                        "1. 🔴 You'll see the declined status in Assignments",
                        "2. 📧 Check if they provided a reason",
                        "3. 🔄 Click **'Reassign'** button for that game",
                        "4. 👥 System will show other available officials",
                        "5. ✅ Assign to a different official",
                        "6. 📧 New official receives notification"
                    ],
                    "tips": [
                        "⚡ Act quickly on declines to ensure game coverage",
                        "📝 Keep notes on why officials decline for future reference"
                    ]
                }
            },
            
            "user_management": {
                "add_user": {
                    "title": "How to Add New Users (Admin Only)",
                    "steps": [
                        "1. 👤 Navigate to **Users** tab (admin access required)",
                        "2. ➕ Click **'Add User'** button", 
                        "3. 📝 Enter user information:",
                        "   • **Username**: Login username",
                        "   • **Password**: Initial password",
                        "   • **Full Name**: User's complete name",
                        "   • **Email**: Contact email",
                        "   • **Role**: Select appropriate role:",
                        "     - 🔑 **Superadmin**: Full system access",
                        "     - 👑 **Admin**: User management, full scheduling",
                        "     - 📊 **Scheduler**: Game and assignment management",
                        "     - 👥 **Official**: View assignments only",
                        "4. 💾 Click **'Create User'**",
                        "5. ✅ User can now log in with provided credentials"
                    ],
                    "security_tips": [
                        "🔐 Use strong temporary passwords",
                        "📧 Send login details securely",
                        "⚠️ Assign minimum necessary role level"
                    ]
                }
            },
            
            "reports_analytics": {
                "generate_reports": {
                    "title": "How to Generate Reports",
                    "steps": [
                        "1. 📊 Go to **Reports** tab",
                        "2. 📋 Choose report type:",
                        "   • **Games Report**: List of games by date range",
                        "   • **Officials Report**: Official activity and performance",
                        "   • **Assignments Report**: Assignment status overview",
                        "   • **League Report**: Games by league",
                        "3. 📅 Set date range for the report",
                        "4. 🎯 Apply any additional filters",
                        "5. 🔄 Click **'Generate Report'**",
                        "6. 📥 Download as PDF or CSV"
                    ]
                }
            },
            
            "navigation_basics": {
                "getting_started": {
                    "title": "Sports Schedulers Navigation Basics",
                    "overview": "Sports Schedulers has a clean sidebar navigation with all main features. Here's how to get around:",
                    "main_sections": [
                        "🏠 **Dashboard**: Overview and quick stats",
                        "🏈 **Games**: Add, edit, and manage all games",
                        "👥 **Officials**: Manage official profiles and information", 
                        "📋 **Assignments**: Assign officials to games and track status",
                        "🏆 **Leagues**: Manage leagues and competitions",
                        "📍 **Locations**: Manage venues and facilities",
                        "📊 **Reports**: Generate various reports and analytics",
                        "👤 **Profile**: Manage your account settings"
                    ],
                    "tips": [
                        "🔍 Use the search function to quickly find specific games or officials",
                        "🎯 Click on any item for detailed view and actions",
                        "📱 Interface is mobile-friendly for on-the-go access",
                        "🔄 Data updates in real-time across all users"
                    ]
                }
            },

            "troubleshooting": {
                "common_issues": {
                    "login_problems": [
                        "✅ Check username and password spelling",
                        "🔐 Ensure Caps Lock is off",
                        "🔄 Try refreshing the page",
                        "📧 Contact admin if account is locked"
                    ],
                    "assignment_conflicts": [
                        "⚠️ Check if official is already assigned to another game at same time",
                        "📍 Verify official's travel radius covers the location",
                        "🏆 Ensure official is certified for that sport/level",
                        "📅 Check if official marked unavailable for that date"
                    ],
                    "csv_import_errors": [
                        "📊 Use the latest CSV template",
                        "📅 Check date format is YYYY-MM-DD",
                        "⏰ Verify time format is HH:MM",
                        "✏️ Remove any empty rows",
                        "🎯 Check sport names match exactly (Basketball, Football, Soccer, etc.)"
                    ]
                }
            },
            
            "quick_tips": {
                "efficiency": [
                    "🚀 Use CSV import for bulk game creation",
                    "⭐ Rate officials after games to improve future assignments",
                    "🔗 Link related games for tournament management",
                    "📱 Set up notifications for real-time updates",
                    "📊 Review reports regularly to identify patterns"
                ],
                "best_practices": [
                    "📅 Schedule games well in advance",
                    "✅ Confirm assignments close to game date",
                    "📧 Keep official contact information updated",
                    "🏆 Track certifications and renewal dates",
                    "🔄 Regularly backup your data"
                ]
            }
        }
    
    def _setup_conversation_patterns(self):
        """Natural language patterns for conversation recognition"""
        return {
            "greetings": [
                r'\b(hi|hello|hey|good\s+(morning|afternoon|evening)|greetings|what\'s\s+up|howdy)\b',
                r'\b(susan|assistant)\b.*\b(hi|hello|hey)\b'
            ],
            "how_are_you": [
                r'\bhow\s+(are\s+you|\'re\s+you|are\s+ya)\b',
                r'\bhow\s+are\s+things\b',
                r'\bhow\s+(is\s+it\s+going|\'s\s+it\s+going)\b'
            ],
            "compliments": [
                r'\b(thank\s+you|thanks|great\s+job|awesome|amazing|wonderful|helpful|smart|good\s+work)\b',
                r'\byou\'re\s+(great|awesome|amazing|helpful|the\s+best|wonderful)\b'
            ],
            "jokes_fun": [
                r'\b(joke|funny|laugh|humor|fun|tell\s+me\s+something\s+(funny|fun))\b',
                r'\bmake\s+me\s+(laugh|smile)\b'
            ]
        }
    
    def _setup_intent_patterns(self):
        """Enhanced intent recognition for Sports Schedulers features"""
        return {
            "add_game": [
                r'\b(add|create|new|make)\s+.*\b(game|match|event)\b',
                r'\bhow\s+(do\s+i|to)\s+(add|create|schedule)\s+.*\b(game|match)\b'
            ],
            "import_games": [
                r'\b(import|upload|csv)\s+.*\b(game|games)\b',
                r'\bcsv\s+(import|upload|file)\b',
                r'\bbulk\s+(import|add|upload)\b'
            ],
            "add_official": [
                r'\b(add|create|new)\s+.*\b(official|referee|umpire)\b',
                r'\bhow\s+(do\s+i|to)\s+(add|create)\s+.*\b(official|ref)\b'
            ],
            "assign_official": [
                r'\b(assign|assignment)\s+.*\b(official|referee)\b',
                r'\bhow\s+(do\s+i|to)\s+(assign|appointment)\b',
                r'\b(official|referee)\s+.*\b(assign|assignment)\b'
            ],
            "view_assignments": [
                r'\b(view|see|check)\s+.*\b(assignment|assignments)\b',
                r'\bassignment\s+(status|list|overview)\b'
            ],
            "add_user": [
                r'\b(add|create|new)\s+.*\buser\b',
                r'\bhow\s+(do\s+i|to)\s+(add|create)\s+.*\buser\b'
            ],
            "reports": [
                r'\b(report|reports|analytics)\b',
                r'\bhow\s+(do\s+i|to)\s+(generate|create|make)\s+.*\breport\b'
            ],
            "navigation": [
                r'\bhow\s+(do\s+i|to)\s+(navigate|use|get\s+around)\b',
                r'\b(where\s+is|how\s+to\s+find)\b',
                r'\bbasics\b'
            ],
            "troubleshooting": [
                r'\b(problem|issue|error|trouble|help|stuck)\b',
                r'\b(not\s+working|broken|can\'t|cannot)\b'
            ]
        }
    
    def _load_emotional_responses(self):
        """Emotional and supportive responses"""
        return {
            "frustrated": [
                "I can sense you might be feeling frustrated! 💙 That's totally normal when learning a new system. Let's break this down step by step. What specific task are you trying to accomplish?",
                "Don't worry - Sports Schedulers can seem complex at first, but once you get the hang of it, it's really intuitive! 🤗 What would you like me to walk you through?"
            ],
            "confused": [
                "No worries about being confused! 😊 Sports Schedulers has lots of features. I'm here to explain everything clearly. What part would you like me to clarify?",
                "Confusion is totally normal! 🌟 Let me break this down into simple steps. What are you trying to do?"
            ],
            "success": [
                "YES! 🎉 You're getting the hang of Sports Schedulers! Great work!",
                "Awesome job! 🌟 You're becoming a Sports Schedulers pro! Keep it up!",
                "Perfect! 💪 You nailed that! Sports Schedulers is so much easier once you know the workflow!"
            ]
        }
    
    def get_user_memory(self, user_id):
        """Get or initialize user conversation memory"""
        if user_id not in self.conversation_memory:
            self.conversation_memory[user_id] = {
                "first_interaction": True,
                "last_seen": None,
                "topics_discussed": [],
                "preferences": {},
                "help_level": "beginner"
            }
        return self.conversation_memory[user_id]
    
    def detect_intent_and_context(self, message, user_role=None):
        """Detect user intent and provide contextual help"""
        message_lower = message.lower()
        
        # Detect conversation type first
        for conv_type, patterns in self.conversation_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    return conv_type, "conversation"
        
        # Detect Sports Schedulers specific intents
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    return intent, "sports_schedulers"
        
        return "general", "sports_schedulers"
    
    def process_message(self, message, user_role="user", user_id=None):
        """Enhanced message processing with real Sports Schedulers knowledge"""
        if not user_id:
            user_id = "default"
            
        user_memory = self.get_user_memory(user_id)
        intent, context_type = self.detect_intent_and_context(message, user_role)
        
        # Update user memory
        user_memory["last_seen"] = datetime.now().isoformat()
        if intent not in user_memory["topics_discussed"]:
            user_memory["topics_discussed"].append(intent)
        
        # Handle conversation
        if context_type == "conversation":
            return self._handle_conversation(intent, message, user_memory)
        else:
            return self._handle_sports_schedulers_help(intent, message, user_role, user_memory)
    
    def _handle_conversation(self, intent, message, user_memory):
        """Handle conversational interactions"""
        if intent == "greetings":
            if user_memory["first_interaction"]:
                user_memory["first_interaction"] = False
                return random.choice(self.knowledge_base["greetings"]["first_time"])
            else:
                current_hour = datetime.now().hour
                if 5 <= current_hour < 12:
                    return random.choice(self.knowledge_base["greetings"]["time_based"]["morning"])
                elif 12 <= current_hour < 17:
                    return random.choice(self.knowledge_base["greetings"]["time_based"]["afternoon"])
                else:
                    return random.choice(self.knowledge_base["greetings"]["time_based"]["evening"])
        
        elif intent == "how_are_you":
            return random.choice(self.knowledge_base["casual_conversation"]["how_are_you"])
        
        elif intent == "compliments":
            return random.choice(self.knowledge_base["casual_conversation"]["compliments"])
        
        elif intent == "jokes_fun":
            return random.choice(self.knowledge_base["casual_conversation"]["jokes_fun"])
        
        return "I love chatting! 😊 What would you like to know about Sports Schedulers?"
    
    def _handle_sports_schedulers_help(self, intent, message, user_role, user_memory):
        """Handle Sports Schedulers specific help requests"""
        
        if intent == "add_game":
            return self._format_procedure_response(
                self.knowledge_base["games_management"]["add_single_game"]
            )
        
        elif intent == "import_games":
            return self._format_procedure_response(
                self.knowledge_base["games_management"]["csv_import"]
            )
        
        elif intent == "add_official":
            return self._format_procedure_response(
                self.knowledge_base["officials_management"]["add_official"]
            )
        
        elif intent == "assign_official":
            return self._format_procedure_response(
                self.knowledge_base["officials_management"]["assign_official"]
            )
        
        elif intent == "view_assignments":
            return self._format_procedure_response(
                self.knowledge_base["assignments_workflow"]["view_assignments"]
            )
        
        elif intent == "add_user":
            if user_role in ["superadmin", "admin"]:
                return self._format_procedure_response(
                    self.knowledge_base["user_management"]["add_user"]
                )
            else:
                return "Adding users requires admin privileges. 🔐 You'll need to ask a system administrator to create new user accounts."
        
        elif intent == "reports":
            return self._format_procedure_response(
                self.knowledge_base["reports_analytics"]["generate_reports"]
            )
        
        elif intent == "navigation":
            return self._format_navigation_help()
        
        elif intent == "troubleshooting":
            return self._handle_troubleshooting(message)
        
        else:
            return self._get_general_help_response(user_role)
    
    def _format_procedure_response(self, procedure_data):
        """Format a procedure into a nice response"""
        response = f"## {procedure_data['title']}\n\n"
        
        if 'overview' in procedure_data:
            response += f"{procedure_data['overview']}\n\n"
        
        if 'steps' in procedure_data:
            response += "**Steps:**\n" + "\n".join(procedure_data['steps']) + "\n\n"
        
        if 'tips' in procedure_data:
            response += "**Pro Tips:**\n" + "\n".join(procedure_data['tips']) + "\n\n"
        
        if 'important' in procedure_data:
            response += f"**Important:** {procedure_data['important']}\n\n"
        
        if 'smart_features' in procedure_data:
            response += "**Smart Features:**\n" + "\n".join(procedure_data['smart_features']) + "\n\n"
        
        response += "Need help with anything else? Just ask! 😊"
        
        return response
    
    def _format_navigation_help(self):
        """Format navigation help response"""
        nav_data = self.knowledge_base["navigation_basics"]["getting_started"]
        
        response = f"## {nav_data['title']}\n\n"
        response += f"{nav_data['overview']}\n\n"
        response += "**Main Sections:**\n" + "\n".join(nav_data['main_sections']) + "\n\n"
        response += "**Navigation Tips:**\n" + "\n".join(nav_data['tips']) + "\n\n"
        response += "Want to learn about any specific section? Just ask! 🎯"
        
        return response
    
    def _handle_troubleshooting(self, message):
        """Handle troubleshooting requests"""
        message_lower = message.lower()
        common_issues = self.knowledge_base["troubleshooting"]["common_issues"]
        
        if "login" in message_lower or "password" in message_lower:
            response = "🔐 **Login Issues - Try These Solutions:**\n\n"
            response += "\n".join(common_issues["login_problems"])
        
        elif "assign" in message_lower or "conflict" in message_lower:
            response = "⚠️ **Assignment Issues - Common Causes:**\n\n"
            response += "\n".join(common_issues["assignment_conflicts"])
        
        elif "csv" in message_lower or "import" in message_lower:
            response = "📊 **CSV Import Problems - Check These:**\n\n"
            response += "\n".join(common_issues["csv_import_errors"])
        
        else:
            response = "🔧 **Common Issues - Quick Fixes:**\n\n"
            response += "**Login Problems:**\n" + "\n".join(common_issues["login_problems"]) + "\n\n"
            response += "**Assignment Conflicts:**\n" + "\n".join(common_issues["assignment_conflicts"]) + "\n\n"
            response += "**CSV Import Errors:**\n" + "\n".join(common_issues["csv_import_errors"])
        
        response += "\n\nStill having trouble? Let me know exactly what's happening and I'll help you solve it! 🛠️"
        return response
    
    def _get_general_help_response(self, user_role):
        """General help response based on user role"""
        if user_role == "official":
            return """Hi! As an official, here's what I can help you with in Sports Schedulers:

📅 **View Your Games**: See all your assigned games and their details
✅ **Respond to Assignments**: Accept or decline game assignments
📱 **Export to Calendar**: Add games to your personal calendar
👤 **Update Profile**: Keep your contact info and availability current

Try asking me:
• "How do I accept a game assignment?"
• "How do I update my availability?"
• "How do I export games to my calendar?"

What would you like to know? 😊"""
        
        else:
            return """I'm here to help you master Sports Schedulers! 🌟 Here's what I can assist with:

🏈 **Games**: Adding single games, CSV import, editing games
👥 **Officials**: Adding officials, managing profiles, certifications
📋 **Assignments**: Assigning officials, tracking responses, handling conflicts
👤 **Users**: Creating accounts, managing roles (admin only)
📊 **Reports**: Generating analytics and data exports
🧭 **Navigation**: Getting around the interface

**Quick Start Ideas:**
• "How do I add a game?"
• "Show me how to assign officials"
• "How to import games via CSV?"
• "Walk me through the basics"

What sounds most helpful? 🎯"""

# Initialize enhanced Susan
susan = SusanSportsSchedulersAssistant()

@assistant_bp.route('/chat', methods=['POST'])
@require_login
def chat_with_susan():
    """Enhanced chat endpoint with real Sports Schedulers knowledge"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({
                'success': False,
                'message': 'Please enter a message'
            }), 400
        
        # Get user info from session
        user_id = session.get('user_id')
        user_role = session.get('role', 'user')
        
        # Process message with enhanced Susan
        response = susan.process_message(user_message, user_role, user_id)
        
        # Log the interaction
        log_activity(
            user_id,
            'chat',
            'assistant',
            None,
            f'Asked Susan: "{user_message[:50]}..."'
        )
        
        return jsonify({
            'success': True,
            'response': response,
            'assistant_name': susan.name,
            'version': susan.version,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error processing request: {str(e)}'
        }), 500

@assistant_bp.route('/memory', methods=['GET'])
@require_login  
def get_conversation_memory():
    """Get user's conversation memory and preferences"""
    try:
        user_id = session.get('user_id')
        memory = susan.get_user_memory(user_id)
        
        return jsonify({
            'success': True,
            'memory': {
                'topics_discussed': memory['topics_discussed'],
                'preferences': memory['preferences'],
                'last_seen': memory['last_seen']
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting memory: {str(e)}'
        }), 500

@assistant_bp.route('/help/<topic>', methods=['GET'])
@require_login
def get_topic_help(topic):
    """Get specific help for a topic"""
    try:
        user_role = session.get('role', 'user')
        
        # Map topic to intent
        topic_map = {
            'games': 'add_game',
            'officials': 'add_official', 
            'assignments': 'assign_official',
            'users': 'add_user',
            'reports': 'reports',
            'navigation': 'navigation'
        }
        
        intent = topic_map.get(topic, 'general')
        response = susan._handle_sports_schedulers_help(intent, f"help with {topic}", user_role, {})
        
        return jsonify({
            'success': True,
            'response': response,
            'topic': topic
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting help: {str(e)}'
        }), 500