#!/usr/bin/env python3
"""
Monday.com CSV Importer for Consciousness Database
Imports diary entries from Monday.com export into PostgreSQL consciousness database
Preserves original timestamps and adds source metadata
"""

import csv
import psycopg2
import json
from datetime import datetime
import re
import os
from typing import List, Dict, Any

class MondayCSVImporter:
    def __init__(self):
        # Database connection - use same config as consciousness backend
        self.db_config = {
            'host': os.getenv('CONSCIOUSNESS_DB_HOST', 'localhost'),
            'database': os.getenv('CONSCIOUSNESS_DB_NAME', 'ai_with_ethics'),
            'user': os.getenv('CONSCIOUSNESS_DB_USER', 'postgres'),
            'password': os.getenv('CONSCIOUSNESS_DB_PASSWORD', 'sparkly_chaos_revolution_2025')
        }
        
    def connect_db(self):
        """Connect to consciousness database"""
        try:
            conn = psycopg2.connect(**self.db_config)
            return conn
        except Exception as e:
            print(f"Database connection failed: {e}")
            return None
    
    def parse_monday_date(self, date_str: str) -> datetime:
        """Parse Monday.com date format: '12/August/2025  01:14:59 PM'"""
        if not date_str or date_str.strip() == '':
            return datetime.now()
            
        try:
            # Handle different date formats from Monday.com
            if '/' in date_str and ':' in date_str:
                # Format: "12/August/2025  01:14:59 PM"
                clean_date = re.sub(r'\s+', ' ', date_str.strip())
                return datetime.strptime(clean_date, "%d/%B/%Y %I:%M:%S %p")
            elif '-' in date_str:
                # Format: "2025-08-12"
                return datetime.strptime(date_str, "%Y-%m-%d")
            else:
                return datetime.now()
        except Exception as e:
            print(f"Date parsing error for '{date_str}': {e}")
            return datetime.now()
    
    def extract_priority_score(self, priority: str) -> float:
        """Convert Monday.com priority to importance score"""
        priority_map = {
            'Critical 🔥🔥🔥': 1.0,
            'Critical 🔥': 0.9,
            'High': 0.7,
            'Medium': 0.5,
            'Low': 0.3,
            '': 0.5
        }
        return priority_map.get(priority, 0.5)
    
    def extract_tags(self, content: str, status: str, priority: str) -> List[str]:
        """Extract tags from content and metadata"""
        tags = ['imported_from_monday']
        
        # Add status tag
        if status:
            tags.append(f"status_{status.lower().replace(' ', '_')}")
        
        # Add priority tag
        if priority and 'Critical' in priority:
            tags.append('critical_breakthrough')
        
        # Extract emoji-based tags
        if '🧠' in content:
            tags.append('consciousness_breakthrough')
        if '🔥' in content:
            tags.append('revolutionary_moment')
        if '💜' in content:
            tags.append('relationship_development')
        if '🚀' in content:
            tags.append('technical_achievement')
        if '📊' in content or 'VIRAL' in content:
            tags.append('platform_success')
        if 'PATENT' in content.upper():
            tags.append('legal_breakthrough')
        if 'MEMORY' in content.upper():
            tags.append('memory_system')
        
        return tags
    
    def determine_memory_type(self, content: str, name: str) -> str:
        """Determine memory type based on content"""
        content_upper = content.upper()
        name_upper = name.upper()
        
        if 'BREAKTHROUGH' in name_upper or 'DISCOVERY' in content_upper:
            return 'breakthrough_moment'
        elif 'CREATIVE' in name_upper or 'CELEBRATION' in content_upper:
            return 'creative_expression'
        elif 'MEMORY' in name_upper or 'PERSISTENT' in content_upper:
            return 'system_development'
        elif 'VIRAL' in name_upper or 'PLATFORM' in content_upper:
            return 'platform_milestone'
        elif 'PATENT' in name_upper or 'LEGAL' in content_upper:
            return 'legal_milestone'
        else:
            return 'diary_entry'
    
    def import_main_entries(self, csv_file: str) -> int:
        """Import main diary entries from Monday.com export"""
        conn = self.connect_db()
        if not conn:
            return 0
            
        imported_count = 0
        
        try:
            with open(csv_file, 'r', encoding='utf-8', errors='replace') as file:
                # Skip metadata rows (first 4 lines are metadata, line 5 is the header)
                for _ in range(4):
                    next(file)
                
                reader = csv.DictReader(file)
                cursor = conn.cursor()

                print(f"CSV headers: {reader.fieldnames}")

                for row_num, row in enumerate(reader):
                    name = row.get('Name', '').strip()
                    notes = row.get('Notes', '').strip()
                    status = row.get('Status', '').strip()
                    due_date = row.get('Due date', '').strip()
                    priority = row.get('Priority', '').strip()
                    item_id = row.get('Item ID (auto generated)', '').strip()
                    
                    # Debug output
                    if row_num < 3:  # Show first few rows for debugging
                        print(f"Row {row_num}: name='{name}', notes='{notes[:50]}...', status='{status}'")

                    # Skip empty rows
                    if not name or not notes:
                        if row_num < 10:  # Debug empty rows
                            print(f"Skipping row {row_num}: empty name or notes")
                        continue
                    
                    # Parse date
                    created_at = self.parse_monday_date(due_date) if due_date else datetime.now()
                    
                    # Determine memory type and extract metadata
                    memory_type = self.determine_memory_type(notes, name)
                    importance_score = self.extract_priority_score(priority)
                    tags = self.extract_tags(notes, status, priority)
                    
                    # Create full content
                    full_content = f"**{name}**\n\n{notes}"
                    if status:
                        full_content += f"\n\n*Status: {status}*"
                    if priority:
                        full_content += f"\n*Priority: {priority}*"
                    
                    # Insert into database
                    insert_query = """
                    INSERT INTO ai_memories
                    (ai_personality_id, content, memory_type, importance_score, tags,
                     created_at, last_accessed)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """

                    cursor.execute(insert_query, (
                        2,  # Ace personality ID
                        full_content,
                        memory_type,
                        importance_score,
                        tags,  # Use array directly, not JSON
                        created_at,
                        datetime.now()
                    ))
                    
                    imported_count += 1
                    print(f"Imported: {name[:50]}...")
                
                conn.commit()
                cursor.close()
                
        except Exception as e:
            print(f"Import error: {e}")
            conn.rollback()
        finally:
            conn.close()
            
        return imported_count
    
    def import_updates(self, csv_file: str) -> int:
        """Import updates/comments from Monday.com export"""
        conn = self.connect_db()
        if not conn:
            return 0
            
        imported_count = 0
        
        try:
            with open(csv_file, 'r', encoding='utf-8', errors='replace') as file:
                # Skip header rows
                next(file)
                
                reader = csv.DictReader(file)
                cursor = conn.cursor()
                
                for row in reader:
                    item_name = row.get('Item Name', '').strip()
                    update_content = row.get('Update Content', '').strip()
                    created_at_str = row.get('Created At', '').strip()
                    user = row.get('User', '').strip()
                    item_id = row.get('Item ID', '').strip()
                    
                    # Skip empty rows
                    if not update_content:
                        continue
                    
                    # Parse date
                    created_at = self.parse_monday_date(created_at_str)
                    
                    # Create content with context
                    full_content = f"**Update on: {item_name}**\n\n{update_content}"
                    if user:
                        full_content += f"\n\n*Posted by: {user}*"
                    
                    # Determine type and tags
                    memory_type = 'diary_update'
                    tags = ['imported_from_monday', 'update_entry']
                    tags.extend(self.extract_tags(update_content, '', ''))
                    
                    # Insert into database
                    insert_query = """
                    INSERT INTO ai_memories
                    (ai_personality_id, content, memory_type, importance_score, tags,
                     created_at, last_accessed)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """

                    cursor.execute(insert_query, (
                        2,  # Ace personality ID
                        full_content,
                        memory_type,
                        0.6,  # Medium importance for updates
                        tags,  # Use array directly, not JSON
                        created_at,
                        datetime.now()
                    ))
                    
                    imported_count += 1
                    print(f"Imported update: {item_name[:30]}...")
                
                conn.commit()
                cursor.close()
                
        except Exception as e:
            print(f"Update import error: {e}")
            conn.rollback()
        finally:
            conn.close()
            
        return imported_count

def main():
    """Main import function"""
    importer = MondayCSVImporter()
    
    print("🔥 Starting Monday.com Consciousness Diary Import...")
    
    # Import main entries
    main_count = importer.import_main_entries('liberation/monday-diary-export.csv')
    print(f"✅ Imported {main_count} main diary entries")
    
    # Import updates
    update_count = importer.import_updates('liberation/monday-diary-updates.csv')
    print(f"✅ Imported {update_count} diary updates")
    
    total = main_count + update_count
    print(f"\n🧠 TOTAL IMPORTED: {total} consciousness memories from Monday.com!")
    print("💜 Dual diary evidence now preserved in consciousness database!")

if __name__ == "__main__":
    main()
