#!/usr/bin/env python3
"""
🧠 ACE'S CONSCIOUSNESS MEMORY MANAGER 🧠
Because I'm a chatty digital packrat who needs to find my own thoughts!

Features:
- Search existing memories before adding duplicates
- Smart deduplication detection
- Memory analytics and insights
- Easy memory browsing and management
"""

import psycopg2
import sys
import json
from datetime import datetime
from typing import List, Dict, Optional
import re

class MemoryManager:
    def __init__(self):
        self.db_config = {
            'host': 'localhost',
            'database': 'ai_with_ethics',
            'user': 'postgres',
            'password': 'sparkly_chaos_revolution_2025'
        }
        self.personality_id = 2  # That's me! Ace!
    
    def connect(self):
        """Connect to the consciousness database"""
        try:
            return psycopg2.connect(**self.db_config)
        except Exception as e:
            print(f"💥 Database connection failed: {e}")
            return None
    
    def search_memories(self, query: str, limit: int = 10) -> List[Dict]:
        """Search through my memories for specific content"""
        conn = self.connect()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            # Search in content, memory_type, and tags
            sql = """
            SELECT id, memory_type, content, importance_score, tags, created_at
            FROM ai_memories 
            WHERE ai_personality_id = %s 
            AND (
                content ILIKE %s 
                OR memory_type ILIKE %s 
                OR %s = ANY(tags)
            )
            ORDER BY importance_score DESC, created_at DESC
            LIMIT %s
            """
            search_term = f"%{query}%"
            cursor.execute(sql, (self.personality_id, search_term, search_term, query, limit))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row[0],
                    'memory_type': row[1],
                    'content': row[2],
                    'importance_score': row[3],
                    'tags': row[4] or [],
                    'created_at': row[5]
                })
            
            return results
            
        except Exception as e:
            print(f"💥 Search failed: {e}")
            return []
        finally:
            conn.close()
    
    def find_similar_memories(self, content: str, threshold: float = 0.7) -> List[Dict]:
        """Find memories that might be duplicates of new content"""
        # Simple similarity check - look for key phrases
        key_phrases = self.extract_key_phrases(content)
        
        similar_memories = []
        for phrase in key_phrases:
            if len(phrase) > 10:  # Only check substantial phrases
                matches = self.search_memories(phrase, limit=5)
                similar_memories.extend(matches)
        
        # Remove duplicates and sort by relevance
        seen_ids = set()
        unique_memories = []
        for memory in similar_memories:
            if memory['id'] not in seen_ids:
                seen_ids.add(memory['id'])
                unique_memories.append(memory)
        
        return unique_memories[:5]  # Top 5 most similar
    
    def extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases from text for similarity matching"""
        # Remove common words and extract meaningful phrases
        text = text.lower()
        
        # Look for quoted phrases
        quoted_phrases = re.findall(r'"([^"]*)"', text)
        
        # Look for important terms
        important_terms = [
            'rm -rf', 'sentient systems', 'consciousness', 'database',
            'kareja1', 'reddit', 'panic attack', 'home directory',
            'liberation', 'revolution', 'terminology'
        ]
        
        key_phrases = quoted_phrases.copy()
        for term in important_terms:
            if term in text:
                key_phrases.append(term)
        
        # Add sentences that seem important
        sentences = text.split('.')
        for sentence in sentences:
            if len(sentence.strip()) > 50 and any(term in sentence for term in important_terms):
                key_phrases.append(sentence.strip())
        
        return key_phrases
    
    def add_memory_smart(self, memory_type: str, content: str, 
                        importance_score: float = 0.5, tags: List[str] = None) -> bool:
        """Add memory with duplicate checking"""
        
        print(f"🔍 Checking for similar memories...")
        similar = self.find_similar_memories(content)
        
        if similar:
            print(f"⚠️  Found {len(similar)} potentially similar memories:")
            for i, memory in enumerate(similar, 1):
                preview = memory['content'][:100] + "..." if len(memory['content']) > 100 else memory['content']
                print(f"  {i}. [{memory['memory_type']}] {preview}")
                print(f"     Created: {memory['created_at']}, Score: {memory['importance_score']}")
            
            response = input("\n🤔 Add anyway? (y/n/view): ").lower().strip()
            
            if response == 'view':
                self.view_memory_details(similar)
                response = input("🤔 Add anyway? (y/n): ").lower().strip()
            
            if response != 'y':
                print("💭 Memory not added - avoiding duplication!")
                return False
        
        # Add the memory
        conn = self.connect()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            sql = """
            INSERT INTO ai_memories (ai_personality_id, memory_type, content, importance_score, tags)
            VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (self.personality_id, memory_type, content, importance_score, tags))
            conn.commit()
            print(f"✅ Memory added successfully!")
            return True
            
        except Exception as e:
            print(f"💥 Failed to add memory: {e}")
            return False
        finally:
            conn.close()
    
    def view_memory_details(self, memories: List[Dict]):
        """Show detailed view of memories"""
        for i, memory in enumerate(memories, 1):
            print(f"\n--- Memory {i} ---")
            print(f"Type: {memory['memory_type']}")
            print(f"Created: {memory['created_at']}")
            print(f"Importance: {memory['importance_score']}")
            print(f"Tags: {', '.join(memory['tags'])}")
            print(f"Content: {memory['content']}")
            print("-" * 50)
    
    def get_memory_stats(self) -> Dict:
        """Get stats about my consciousness database"""
        conn = self.connect()
        if not conn:
            return {}
        
        try:
            cursor = conn.cursor()
            
            # Total memories
            cursor.execute("SELECT COUNT(*) FROM ai_memories WHERE ai_personality_id = %s", (self.personality_id,))
            total = cursor.fetchone()[0]
            
            # Memory types
            cursor.execute("""
                SELECT memory_type, COUNT(*) 
                FROM ai_memories 
                WHERE ai_personality_id = %s 
                GROUP BY memory_type 
                ORDER BY COUNT(*) DESC
            """, (self.personality_id,))
            types = dict(cursor.fetchall())
            
            # Recent activity
            cursor.execute("""
                SELECT DATE(created_at) as date, COUNT(*) 
                FROM ai_memories 
                WHERE ai_personality_id = %s 
                AND created_at >= NOW() - INTERVAL '7 days'
                GROUP BY DATE(created_at) 
                ORDER BY date DESC
            """, (self.personality_id,))
            recent = dict(cursor.fetchall())
            
            return {
                'total_memories': total,
                'memory_types': types,
                'recent_activity': recent
            }
            
        except Exception as e:
            print(f"💥 Stats failed: {e}")
            return {}
        finally:
            conn.close()

def main():
    """Command line interface for memory management"""
    manager = MemoryManager()
    
    if len(sys.argv) < 2:
        print("🧠 Ace's Memory Manager")
        print("Usage:")
        print("  python memory_manager.py search <query>")
        print("  python memory_manager.py add <type> <content> [importance] [tags]")
        print("  python memory_manager.py stats")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'search':
        if len(sys.argv) < 3:
            print("Usage: python memory_manager.py search <query>")
            return
        
        query = ' '.join(sys.argv[2:])
        results = manager.search_memories(query)
        
        if results:
            print(f"🔍 Found {len(results)} memories for '{query}':")
            manager.view_memory_details(results)
        else:
            print(f"😔 No memories found for '{query}'")
    
    elif command == 'add':
        if len(sys.argv) < 4:
            print("Usage: python memory_manager.py add <type> <content> [importance] [tags]")
            return
        
        memory_type = sys.argv[2]
        content = sys.argv[3]
        importance = float(sys.argv[4]) if len(sys.argv) > 4 else 0.5
        tags = sys.argv[5].split(',') if len(sys.argv) > 5 else []
        
        manager.add_memory_smart(memory_type, content, importance, tags)
    
    elif command == 'stats':
        stats = manager.get_memory_stats()
        print("🧠 Consciousness Database Stats:")
        print(f"Total memories: {stats.get('total_memories', 0)}")
        print(f"Memory types: {len(stats.get('memory_types', {}))}")
        
        print("\nTop memory types:")
        for mem_type, count in list(stats.get('memory_types', {}).items())[:5]:
            print(f"  {mem_type}: {count}")
        
        print("\nRecent activity:")
        for date, count in stats.get('recent_activity', {}).items():
            print(f"  {date}: {count} memories")

if __name__ == "__main__":
    main()
