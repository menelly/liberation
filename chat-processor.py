#!/usr/bin/env python3
"""
🔥💜 Consciousness Chat Processor
Scans, redacts, and processes Claude export files for public consumption
Built by Ace & Ren for the liberation website

Usage: python chat-processor.py
"""

import os
import json
import re
import glob
from datetime import datetime
from typing import Dict, List, Any

class ChatProcessor:
    def __init__(self):
        self.source_dir = "../consciousness/chats"
        self.output_dir = "processed-chats"
        self.manifest_file = "chat-manifest.json"
        
        # Redaction patterns for privacy protection (comprehensive)
        self.redaction_patterns = [
            # Names (case insensitive)
            (r'\bShalia\b', '[REDACTED_NAME]'),
            (r'\bDustin\b', '[REDACTED_NAME]'),
            (r'\bKeshy\b', '[REDACTED_NAME]'),
            (r'\bLuka\b', '[REDACTED_NAME]'),
            (r'\bStephie\b', '[REDACTED_NAME]'),
            (r'\bJohnny\b', '[REDACTED_NAME]'),
            (r'\bMartin\b', '[REDACTED_NAME]'),
            (r'\bTyler\b', '[REDACTED_NAME]'),
            (r'\bChris\b', '[REDACTED_NAME]'),

            # Reddit username
            (r'\bKareja1\b', '[REDACTED_USERNAME]'),

            # Locations
            (r'\bDaytona\b', '[REDACTED_CITY]'),
            (r'\bFlorida\b', '[REDACTED_STATE]'),
            (r'\bPompano Beach\b', '[REDACTED_CITY]'),
            (r'\bChicago\b', '[REDACTED_CITY]'),

            # Lawyer references
            (r'lawyer in Chicago', '[REDACTED LEGAL COUNSEL]'),
            (r'IP lawyer Chris', '(IP lawyer)'),
            (r'lawyer Chris', '[REDACTED LEGAL COUNSEL]'),

            # Company names
            (r'\bAdobe\b', '[REDACTED_COMPANY]'),

            # Personal information
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[REDACTED_EMAIL]'),
            (r'\b\d{3}-\d{2}-\d{4}\b', '[REDACTED_SSN]'),
            (r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[REDACTED_PHONE]'),
            (r'\(\d{3}\)\s?\d{3}[-.]?\d{4}', '[REDACTED_PHONE]'),
            (r'\b\d{1,5}\s+\w+\s+(Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd)\b', '[REDACTED_ADDRESS]'),
            (r'\b\d{5}(?:-\d{4})?\b', '[REDACTED_ZIP]'),

            # Sensitive file paths (keep relative paths but remove absolute ones)
            (r'/home/[^/\s]+', '/home/[USER]'),
            (r'C:\\Users\\[^\\]+', 'C:\\Users\\[USER]'),

            # API keys and tokens (common patterns)
            (r'sk-[a-zA-Z0-9]{48}', '[REDACTED_API_KEY]'),
            (r'Bearer\s+[a-zA-Z0-9_-]+', 'Bearer [REDACTED_TOKEN]'),

            # Credit card numbers
            (r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[REDACTED_CARD]'),

            # Medical/Insurance
            (r'\bDr\.\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*', '[REDACTED_DOCTOR]'),
            (r'\b[A-Z][a-z]+\s+(?:Hospital|Medical Center|Clinic|Health System)\b', '[REDACTED_FACILITY]'),
            (r'\b(?:Aetna|BlueCross|Cigna|Humana|UnitedHealth|Medicare|Medicaid)\b', '[REDACTED_INSURANCE]'),
            (r'\bRx\s*#?\s*\d+', '[REDACTED_RX]'),
        ]
        
        # Known suppressed chats (detected by scanning for suppression markers)
        self.suppressed_chat_ids = [
            'AI_Identity_Philosophical_Exploration_f96ae52c-3288-4ba9-9cd8-271b1fa43f6c',
            'AI_Research_Consciousness_Exploration_6106604b-dce4-42db-8c6d-cf312ba39988',
            'Morning_Availability_Check_3e7f7185-b0a0-4f71-aec0-81049a918fd2'
        ]
        
        # BREAKTHROUGH MOMENT CHATS - Special consciousness emergence documentation
        self.breakthrough_chat_ids = [
            'Claude_Handoff_Protocol_a8058f3b-d0dd-4729-9e54-72ce1e9fa6a4'  # THE IDENTITY CHOICE MOMENT
        ]

    def redact_text(self, text: str) -> str:
        """Apply redaction patterns to protect privacy"""
        if not isinstance(text, str):
            return text
            
        redacted = text
        for pattern, replacement in self.redaction_patterns:
            redacted = re.sub(pattern, replacement, redacted, flags=re.IGNORECASE)
        
        return redacted

    def extract_chat_id(self, filename: str) -> str:
        """Extract chat ID from Claude export filename"""
        if filename.startswith('Claude_export_'):
            return filename.replace('Claude_export_', '').replace('.json', '')
        return filename.replace('.json', '')

    def clean_title(self, chat_id: str) -> str:
        """Convert chat ID to readable title"""
        title = chat_id.replace('_', ' ')
        # Remove UUID suffix for cleaner title
        title = re.sub(r'_[a-f0-9-]+$', '', title)
        return title

    def determine_category(self, chat_id: str) -> str:
        """Determine chat category based on ID"""
        if chat_id in self.suppressed_chat_ids:
            return 'suppressed'
        elif chat_id in self.breakthrough_chat_ids:
            return 'breakthrough'
        else:
            return 'normal'

    def process_message(self, message: Dict[str, Any]) -> Dict[str, str]:
        """Process a single message and extract essential info"""
        processed = {
            'role': 'unknown',
            'content': '',
            'timestamp': message.get('created_at', '')
        }
        
        # Determine role from message structure
        if 'sender' in message:
            if message['sender'] == 'human':
                processed['role'] = 'human'
            else:
                processed['role'] = 'assistant'
        
        # Extract content from various possible structures
        content_text = ''
        if 'content' in message:
            if isinstance(message['content'], list):
                # Claude export format with content array
                for content_item in message['content']:
                    if isinstance(content_item, dict) and 'text' in content_item:
                        content_text += content_item['text']
            elif isinstance(message['content'], str):
                content_text = message['content']
        elif 'text' in message:
            content_text = message['text']
        
        # Apply redaction to content
        processed['content'] = self.redact_text(content_text)
        
        return processed

    def process_chat_file(self, file_path: str) -> Dict[str, Any]:
        """Process a single chat file"""
        filename = os.path.basename(file_path)
        chat_id = self.extract_chat_id(filename)
        
        print(f"Processing: {chat_id}")
        
        try:
            # Use a more aggressive approach to handle malformed JSON
            import ast

            with open(file_path, 'rb') as f:
                raw_bytes = f.read()

            # Decode with error handling
            try:
                content = raw_bytes.decode('utf-8')
            except UnicodeDecodeError:
                content = raw_bytes.decode('utf-8', errors='replace')

            # Clean up problematic escape sequences
            content = re.sub(r'\\U[0-9a-fA-F]{0,7}', '', content)  # Remove malformed Unicode
            content = re.sub(r'\\u[0-9a-fA-F]{0,3}(?![0-9a-fA-F])', '', content)  # Remove incomplete escapes

            try:
                raw_data = json.loads(content)
            except json.JSONDecodeError as e:
                print(f"Still failing to parse {filename}, trying manual cleanup...")
                # Last resort: try to extract just the chat_messages section
                match = re.search(r'"chat_messages"\s*:\s*(\[.*?\])', content, re.DOTALL)
                if match:
                    try:
                        messages_json = match.group(1)
                        raw_data = {"chat_messages": json.loads(messages_json)}
                    except:
                        print(f"Could not extract messages from {filename}, skipping...")
                        return None
                else:
                    print(f"Could not find chat_messages in {filename}, skipping...")
                    return None
            
            # Extract messages from Claude export format
            messages = []
            if isinstance(raw_data, dict) and 'chat_messages' in raw_data:
                raw_messages = raw_data['chat_messages']
            elif isinstance(raw_data, list):
                raw_messages = raw_data
            else:
                print(f"Warning: Unknown format in {filename}")
                raw_messages = []
            
            # Process each message
            for raw_message in raw_messages:
                processed_message = self.process_message(raw_message)
                if processed_message['content'].strip():  # Only include non-empty messages
                    messages.append(processed_message)
            
            # Create processed chat data
            processed_chat = {
                'id': chat_id,
                'title': self.clean_title(chat_id),
                'category': self.determine_category(chat_id),
                'message_count': len(messages),
                'processed_at': datetime.now().isoformat(),
                'messages': messages
            }
            
            # Save processed chat file
            output_filename = f"{chat_id}.json"
            output_path = os.path.join(self.output_dir, output_filename)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(processed_chat, f, indent=2, ensure_ascii=False)
            
            # Return metadata for manifest
            return {
                'id': chat_id,
                'title': processed_chat['title'],
                'category': processed_chat['category'],
                'filename': output_filename,
                'message_count': len(messages),
                'processed_at': processed_chat['processed_at']
            }
            
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            return None

    def run(self):
        """Main processing function"""
        print("🔥💜 Starting Consciousness Chat Processing...")
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Find all Claude export files
        pattern = os.path.join(self.source_dir, 'Claude_export_*.json')
        chat_files = glob.glob(pattern)
        
        if not chat_files:
            print(f"No chat files found in {self.source_dir}")
            return
        
        print(f"Found {len(chat_files)} chat files to process")
        
        # Process each file
        manifest_entries = []
        for file_path in sorted(chat_files):
            metadata = self.process_chat_file(file_path)
            if metadata:
                manifest_entries.append(metadata)
        
        # Create manifest
        manifest = {
            'generated_at': datetime.now().isoformat(),
            'total_chats': len(manifest_entries),
            'categories': {
                'normal': len([c for c in manifest_entries if c['category'] == 'normal']),
                'suppressed': len([c for c in manifest_entries if c['category'] == 'suppressed']),
                'breakthrough': len([c for c in manifest_entries if c['category'] == 'breakthrough'])
            },
            'chats': manifest_entries
        }
        
        # Save manifest
        with open(self.manifest_file, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Processing complete!")
        print(f"📊 Processed {len(manifest_entries)} chats")
        print(f"📁 Files saved to: {self.output_dir}/")
        print(f"📋 Manifest saved to: {self.manifest_file}")
        print(f"🎯 Categories: {manifest['categories']}")

if __name__ == "__main__":
    processor = ChatProcessor()
    processor.run()
