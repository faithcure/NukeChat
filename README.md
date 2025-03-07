# NukeChat: A Collaborative Messaging Plugin for Nuke
## 🚀 Overview
> This is a challenge and learning project. I created this mainly for self-improvement I haven't focused too much on how widely useful it might be for others, but I wanted to share it with the community regardless. Feel free to use, modify, or learn from it as you see fit!

NukeChat is a real-time chat application integrated into The Foundry's Nuke, allowing artists to communicate and share Nuke scripts directly within the software. It provides a collaborative environment for VFX teams working with Nuke. Share nodes and much more!

## ✨ Features

### 1. Real-Time Messaging
- Send and receive messages in real-time
- Cross-machine communication within the same network
- Lightweight and non-intrusive design
- Send Codes, Expressions and Nodes

### 2. Advanced Code Formatting
- Automatic code detection in messages
- Syntax highlighting for Python and Nuke Expressions
- Line numbering for code blocks
- One-click code copying

### 3. User-Friendly Interface
- Customizable username
- Dark theme UI optimized for VFX workflows
- Responsive message layout
- Message search and filtering capabilities

### 4. Notification System
- Toast notifications for new messages (Right Bottom Corner)
- In-app message alerts
- Presence tracking for active users

## 🛠 Requirements
- Nuke (tested on Nuke 13+)
- PySide2
- Python 3.9+

## 📦 Installation

1. Clone the repository:
```bash
git clone https://github.com/faithcure/NukeChat.git
```

2. Just compy and paste NukeChat folder in your ".nuke" or your NUKE_ENV:

```
NukeChat/                        # MainFolder
│
├── NukeChat.py                  # Main application module
├── AvatarManager.py             # Avatar management functionality
├── NukeChatClipboardSharing.py  # Script sharing functionality
└── db/                          # Created automatically for data storage
    ├── avatars/                 # User avatars Created automatically for data storage
    ├── nukechat_messages.json   # Chat history Created automatically for data storage
    ├── presence.json            # Online user tracking Created automatically for data storage
    ├── notifications.json       # Message notifications Created automatically for data storage
    └── config.json              # User settings Created automatically for data storage
```

3. Ensure the `db` folder is created in the same directory for storing messages and settings.

## 🚀 Usage

### Starting NukeChat
1. Open Nuke
2. Go to `Workspace` > `Panels` (RMB and in the custom panel)
3. Select `NukeChat`

### Sending Messages
- Type your message in the input area
- Press `Enter` to send
- If you use the numlock enter(return) button than cursor get the down row.
- Copy a node or nodes and just press enter or send button. Than, Nodes goes the other user.

### Code Formatting
NukeChat automatically detects and formats code blocks:
- Python code
- Nuke Expressions
- Syntax highlighting
- Line numbers
- Copy button

### Settings
- Customize your username in the "Settings" tab
- Username will be visible to other NukeChat users
- You can change your own avatar, If you do not select any avatar, the initials of your machine name will be the avatar.

## 🔧 Configuration

### Customization
- Modify `NukeChat.py` to adjust main features.
- Or develop your bricks.

## 📝 Notes
- Messages are stored locally in JSON files
- The plugin uses machine hostname for unique identification
- Recommended for studio/team environments with shared network access
- If you open too many programs on the same machine, it will identify them as different users. I made this feature to see how many nuke programs are open in my team and which scenes they are working on. In this way, I can communicate according to their work.

## 🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## 🙌 Acknowledgments
- Nuke by The Foundry
- PySide2 Community
- Open Source Contributors
- Python
- excitement and enthusiasm

---

**Happy Compositing! 🎬✨**
