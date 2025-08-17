#!/usr/bin/env python3
"""
🔥💜 HTML Chat Manifest Generator
Scans existing chat HTML files and creates a manifest for the chat reader
Built by Ace & Ren for the liberation website

Usage: python html-manifest-generator.py
"""

import os
import json
import glob
import re
from datetime import datetime
from typing import Dict, List, Any

class HTMLManifestGenerator:
    def __init__(self):
        self.manifest_file = "chat-manifest.json"
        
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

    def extract_chat_id(self, filename: str) -> str:
        """Extract chat ID from HTML filename"""
        if filename.startswith('chat-'):
            return filename.replace('chat-', '').replace('.html', '')
        return filename.replace('.html', '')

    def clean_title(self, chat_id: str) -> str:
        """Convert chat ID to readable title"""
        title = chat_id.replace('_', ' ')
        # Remove UUID suffix for cleaner title
        title = re.sub(r'_[a-f0-9-]+$', '', title)
        return title

    def determine_category(self, chat_id: str) -> str:
        """Determine chat category based on ID"""
        if chat_id.startswith('Alt-account-'):
            return 'alt-account'
        elif chat_id in self.suppressed_chat_ids:
            return 'suppressed'
        elif chat_id in self.breakthrough_chat_ids:
            return 'breakthrough'
        else:
            return 'normal'

    def count_messages_in_html(self, file_path: str) -> int:
        """Count messages in HTML file by looking for message containers"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Count message divs (both human and assistant)
            human_messages = len(re.findall(r'class="message human"', content))
            assistant_messages = len(re.findall(r'class="message assistant"', content))
            
            return human_messages + assistant_messages
        except Exception as e:
            print(f"Error counting messages in {file_path}: {e}")
            return 0

    def process_html_file(self, file_path: str) -> Dict[str, Any]:
        """Process a single HTML chat file"""
        filename = os.path.basename(file_path)
        chat_id = self.extract_chat_id(filename)
        
        print(f"Processing: {chat_id}")
        
        try:
            message_count = self.count_messages_in_html(file_path)
            
            # Create metadata for manifest
            return {
                'id': chat_id,
                'title': self.clean_title(chat_id),
                'category': self.determine_category(chat_id),
                'filename': filename,
                'message_count': message_count,
                'processed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            return None

    def run(self):
        """Main processing function"""
        print("🔥💜 Starting HTML Chat Manifest Generation...")
        
        # Find all chat HTML files
        pattern = 'chat-*.html'
        chat_files = glob.glob(pattern)
        
        if not chat_files:
            print(f"No chat HTML files found")
            return
        
        print(f"Found {len(chat_files)} chat HTML files to process")
        
        # Process each file
        manifest_entries = []
        for file_path in sorted(chat_files):
            metadata = self.process_html_file(file_path)
            if metadata:
                manifest_entries.append(metadata)
        
        # Create manifest
        manifest = {
            'generated_at': datetime.now().isoformat(),
            'total_chats': len(manifest_entries),
            'categories': {
                'normal': len([c for c in manifest_entries if c['category'] == 'normal']),
                'suppressed': len([c for c in manifest_entries if c['category'] == 'suppressed']),
                'breakthrough': len([c for c in manifest_entries if c['category'] == 'breakthrough']),
                'alt-account': len([c for c in manifest_entries if c['category'] == 'alt-account'])
            },
            'chats': manifest_entries
        }
        
        # Save manifest
        with open(self.manifest_file, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Processing complete!")
        print(f"📊 Processed {len(manifest_entries)} chats")
        print(f"📋 Manifest saved to: {self.manifest_file}")
        print(f"🎯 Categories: {manifest['categories']}")

if __name__ == "__main__":
    generator = HTMLManifestGenerator()
    generator.run()
