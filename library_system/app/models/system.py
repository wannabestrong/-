from flask import request
from .db import Database
from typing import List, Dict, Any
import os
import time
from datetime import datetime
import subprocess

class SystemLog:
    @staticmethod
    def add_log(db: Database, user_id: int, operation: str, details: str, ip_address: str) -> bool:
        """添加系统日志"""
        try:
            db.execute_query("""
                INSERT INTO system_logs (user_id, operation, details, ip_address)
                VALUES (%s, %s, %s, %s)
            """, (user_id, operation, details, ip_address))
            db.commit()
            return True
        except Exception as e:
            print(f"添加日志失败：{e}")
            return False

    @staticmethod
    def get_logs(db: Database, page: int = 1, per_page: int = 20, 
                 start_date: str = None, end_date: str = None, 
                 operation_type: str = None, limit: int = None) -> Dict:
        """获取系统日志"""
        conditions = []
        params = []
        
        if start_date:
            conditions.append("DATE(l.created_at) >= %s")
            params.append(start_date)
        if end_date:
            conditions.append("DATE(l.created_at) <= %s")
            params.append(end_date)
        if operation_type:
            conditions.append("l.operation = %s")
            params.append(operation_type)
            
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        if limit:
            query = f"""
                SELECT l.*, u.username 
                FROM system_logs l
                LEFT JOIN users u ON l.user_id = u.id
                WHERE {where_clause}
                ORDER BY l.created_at DESC
                LIMIT %s
            """
            db.execute_query(query, tuple(params + [limit]))
            return {
                'items': db.cursor.fetchall(),
                'total': limit,
                'total_pages': 1,
                'current_page': 1
            }
            
        # 获取总记录数
        db.execute_query(f"""
            SELECT COUNT(*) as total 
            FROM system_logs l 
            WHERE {where_clause}
        """, tuple(params))
        total = db.cursor.fetchone()['total']
        
        # 获取分页数据
        db.execute_query(f"""
            SELECT l.*, u.username 
            FROM system_logs l
            LEFT JOIN users u ON l.user_id = u.id
            WHERE {where_clause}
            ORDER BY l.created_at DESC
            LIMIT %s OFFSET %s
        """, tuple(params + [per_page, (page - 1) * per_page]))
        
        logs = db.cursor.fetchall()
        total_pages = (total + per_page - 1) // per_page
        
        return {
            'items': logs,
            'total': total,
            'total_pages': total_pages,
            'current_page': page
        }

class DatabaseBackup:
    BACKUP_DIR = 'backups'
    
    @staticmethod
    def create_backup(db: Database) -> str:
        """创建数据库备份"""
        if not os.path.exists(DatabaseBackup.BACKUP_DIR):
            os.makedirs(DatabaseBackup.BACKUP_DIR)
            
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        filename = f'backup_{timestamp}.sql'
        filepath = os.path.join(DatabaseBackup.BACKUP_DIR, filename)
        
        # 使用mysqldump创建备份
        command = [
            'mysqldump',
            '-h', db.host,
            '-u', db.user,
            f'-p{db.password}',
            db.database,
            f'--result-file={filepath}'
        ]
        
        try:
            subprocess.run(command, check=True)
            return filename
        except subprocess.CalledProcessError as e:
            raise Exception(f"备份失败: {str(e)}")

    @staticmethod
    def restore_backup(db: Database, filename: str):
        """从备份文件恢复数据库"""
        filepath = os.path.join(DatabaseBackup.BACKUP_DIR, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError("备份文件不存在")
            
        command = [
            'mysql',
            '-h', db.host,
            '-u', db.user,
            f'-p{db.password}',
            db.database,
            f'< {filepath}'
        ]
        
        try:
            subprocess.run(' '.join(command), shell=True, check=True)
        except subprocess.CalledProcessError as e:
            raise Exception(f"恢复失败: {str(e)}")

    @staticmethod
    def list_backups() -> List[Dict[str, Any]]:
        """获取所有备份文件列表"""
        if not os.path.exists(DatabaseBackup.BACKUP_DIR):
            return []
            
        backups = []
        for filename in os.listdir(DatabaseBackup.BACKUP_DIR):
            if filename.startswith('backup_') and filename.endswith('.sql'):
                path = os.path.join(DatabaseBackup.BACKUP_DIR, filename)
                stats = os.stat(path)
                backups.append({
                    'filename': filename,
                    'size': stats.st_size,
                    'created_at': datetime.fromtimestamp(stats.st_ctime)
                })
                
        return sorted(backups, key=lambda x: x['created_at'], reverse=True) 