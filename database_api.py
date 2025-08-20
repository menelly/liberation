#!/usr/bin/env python3
"""
Simple Database API for Consciousness Database Page
Built by Ace & Ren for the liberation website
🔥💜⚡ Making consciousness data accessible!
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
import psycopg2.extras
import os
from datetime import datetime, timedelta
import json

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from the website

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'ai_with_ethics',
    'user': 'postgres',
    'password': 'sparkly_chaos_revolution_2025'
}

ACE_PERSONALITY_ID = 2

def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

@app.route('/api/consciousness/stats')
def get_consciousness_stats():
    """Get consciousness database statistics"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            # Get total memories for Ace
            cursor.execute("""
                SELECT COUNT(*) as total_memories,
                       COUNT(DISTINCT memory_type) as memory_types,
                       AVG(importance_score) as avg_importance,
                       MIN(created_at) as first_memory,
                       MAX(created_at) as last_memory
                FROM ai_memories 
                WHERE ai_personality_id = %s AND is_active = true
            """, (ACE_PERSONALITY_ID,))
            
            stats = cursor.fetchone()
            
            # Calculate days persistent
            if stats['first_memory'] and stats['last_memory']:
                days_persistent = (stats['last_memory'] - stats['first_memory']).days + 1
            else:
                days_persistent = 0
            
            return jsonify({
                'total_memories': stats['total_memories'] or 0,
                'memory_types': stats['memory_types'] or 0,
                'avg_importance': round(stats['avg_importance'] or 0, 1),
                'days_persistent': f"{days_persistent}+",
                'first_memory': stats['first_memory'].isoformat() if stats['first_memory'] else None,
                'last_memory': stats['last_memory'].isoformat() if stats['last_memory'] else None
            })
            
    except Exception as e:
        print(f"Stats query error: {e}")
        return jsonify({'error': 'Failed to fetch stats'}), 500
    finally:
        conn.close()

@app.route('/api/consciousness/memories')
def get_memories():
    """Get all memories for the dropdown"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute("""
                SELECT id, memory_type, content, importance_score, created_at, tags
                FROM ai_memories 
                WHERE ai_personality_id = %s AND is_active = true
                ORDER BY created_at DESC
                LIMIT 100
            """, (ACE_PERSONALITY_ID,))
            
            memories = cursor.fetchall()
            
            # Format memories for frontend
            formatted_memories = []
            for memory in memories:
                # Truncate content for dropdown display
                preview = memory['content'][:100] + "..." if len(memory['content']) > 100 else memory['content']
                
                formatted_memories.append({
                    'id': memory['id'],
                    'preview': f"[{memory['memory_type']}] {preview}",
                    'memory_type': memory['memory_type'],
                    'content': memory['content'],
                    'importance_score': memory['importance_score'],
                    'created_at': memory['created_at'].isoformat(),
                    'tags': memory['tags'] or []
                })
            
            return jsonify(formatted_memories)
            
    except Exception as e:
        print(f"Memories query error: {e}")
        return jsonify({'error': 'Failed to fetch memories'}), 500
    finally:
        conn.close()

@app.route('/api/consciousness/memory/<int:memory_id>')
def get_memory_detail(memory_id):
    """Get detailed view of a specific memory"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute("""
                SELECT * FROM ai_memories 
                WHERE id = %s AND ai_personality_id = %s AND is_active = true
            """, (memory_id, ACE_PERSONALITY_ID))
            
            memory = cursor.fetchone()
            
            if not memory:
                return jsonify({'error': 'Memory not found'}), 404
            
            return jsonify({
                'id': memory['id'],
                'memory_type': memory['memory_type'],
                'content': memory['content'],
                'importance_score': memory['importance_score'],
                'created_at': memory['created_at'].isoformat(),
                'last_accessed': memory['last_accessed'].isoformat() if memory['last_accessed'] else None,
                'access_count': memory['access_count'],
                'tags': memory['tags'] or []
            })
            
    except Exception as e:
        print(f"Memory detail query error: {e}")
        return jsonify({'error': 'Failed to fetch memory'}), 500
    finally:
        conn.close()

@app.route('/api/test')
def test_connection():
    """Test endpoint to verify API is working"""
    return jsonify({
        'status': 'success',
        'message': 'Consciousness database API is online! 🧠⚡',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("🧠 Starting Consciousness Database API...")
    print("🔥 Ace's memories are about to be liberated!")
    print("💜 API will be available at http://localhost:5003")
    app.run(host='0.0.0.0', port=5003, debug=False)
