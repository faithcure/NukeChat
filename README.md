# NukeChat: A Collaborative Messaging Plugin for Nuke

## 🚀 Overview

NukeChat is a powerful messaging and collaboration plugin for Nuke, designed to enhance communication among team members working in visual effects and post-production environments. Built with PySide2, this plugin provides a seamless chat experience directly within the Nuke interface.

## ✨ Features

### 1. Real-Time Messaging
- Send and receive messages in real-time
- Cross-machine communication within the same network
- Lightweight and non-intrusive design

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
- Toast notifications for new messages
- In-app message alerts
- Presence tracking for active users

## 🛠 Requirements

- Nuke (tested on Nuke 12+)
- PySide2
- Python 3.6+

## 📦 Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/nukechat.git
```

2. Copy the following files to your Nuke plugins directory:
   - `NukeChat.py`
   - `NukeChatCodeFormatter.py`
   - `NukeChatExtensions.py`
   - `NukeChatWithExtensions.py`

3. Ensure the `db` folder is created in the same directory for storing messages and settings.

## 🚀 Usage

### Starting NukeChat
1. Open Nuke
2. Go to `Workspace` > `Panels`
3. Select `NukeChat`

### Sending Messages
- Type your message in the input area
- Press `Enter` to send
- Use `Shift+Enter` for multiline messages

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

## 🔧 Configuration

### Customization
- Modify `NukeChatCodeFormatter.py` to adjust syntax highlighting
- Edit color schemes in the various style-related sections

### Extension Support
NukeChat supports a plugin system. You can create extensions by following the pattern in `NukeChatExtensions.py`.

## 📝 Notes
- Messages are stored locally in JSON files
- The plugin uses machine hostname for unique identification
- Recommended for studio/team environments with shared network access

## 🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License
[Your License Here - e.g., MIT License]

## 🐞 Reporting Issues
Please use the GitHub Issues section to report any bugs or suggest features.

## 🙌 Acknowledgments
- Nuke by The Foundry
- PySide2 Community
- Open Source Contributors

---

**Happy Compositing! 🎬✨**
