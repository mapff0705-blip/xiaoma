import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List
from threading import Lock
import mysql.connector
from mysql.connector import Error

# 设置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 创建一个锁，用于保护数据库操作的线程安全
jobs_lock = Lock()

# 创建MySQL数据库连接函数，确保连接在操作前是可用的
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='123456',
        )
        if conn.is_connected():
            cursor = conn.cursor()
            # 创建数据库（如果不存在）
            cursor.execute("CREATE DATABASE IF NOT EXISTS crewai CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            cursor.close()
            conn.close()

            # 再次连接，这次指定数据库
            conn = mysql.connector.connect(
                host='localhost',
                user='root',
                password='123456',
                database='crewai'
            )
            return conn
    except Error as e:
        logging.error(f"Error connecting to MySQL: {e}")
        return None

# 初始化连接
conn = get_db_connection()
if conn:
    cursor = conn.cursor()
    # 创建 jobs 和 events 表（如果它们不存在）
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                job_id VARCHAR(255) PRIMARY KEY,
                status VARCHAR(50),
                result TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INT AUTO_INCREMENT PRIMARY KEY,
                job_id VARCHAR(255),
                timestamp DATETIME,
                data TEXT,
                FOREIGN KEY (job_id) REFERENCES jobs(job_id)
            )
        ''')
        conn.commit()
    except Error as e:
        logging.error(f"Error creating tables: {e}")
else:
    logging.critical("Failed to establish initial connection to MySQL.")

# 定义一个 Event 类，表示事件的结构
@dataclass
class Event:
    timestamp: datetime
    data: str

# 定义一个 Job 类，表示一个作业的结构
@dataclass
class Job:
    status: str
    events: List[Event]
    result: str

# 定义函数 append_event，接受 job_id 和事件数据 event_data 作为参数
def append_event(job_id: str, event_data: str):
    with jobs_lock:
        try:
            # 确保数据库连接有效
            conn = get_db_connection()
            if conn is None:
                raise Exception("Database connection is not available.")

            cursor = conn.cursor()

            # 检查 jobs 表中是否存在 job_id
            cursor.execute("SELECT job_id FROM jobs WHERE job_id = %s", (job_id,))
            job = cursor.fetchone()

            if job is None:
                # 如果不存在，创建一个新的 Job 记录
                logging.info(f"Job {job_id} started")
                cursor.execute("INSERT INTO jobs (job_id, status, result) VALUES (%s, %s, %s)",
                               (job_id, 'STARTED', ''))
            else:
                logging.info(f"Appending event for job {job_id}: {event_data}")

            # 创建一个新的 Event 记录
            cursor.execute("INSERT INTO events (job_id, timestamp, data) VALUES (%s, %s, %s)",
                           (job_id, datetime.now(), event_data))

            # 提交事务以保存对数据库的更改
            conn.commit()

        except Error as e:
            logging.error(f"Error appending event for job {job_id}: {e}")
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()


# 定义函数 update_job_by_id，根据 job_id 更新 status、result 和 events
def update_job_by_id(job_id: str, status: str, result: str, event_data: List[str]):
    with jobs_lock:
        try:
            # 确保数据库连接有效
            conn = get_db_connection()
            if conn is None:
                raise Exception("Database connection is not available.")

            cursor = conn.cursor()

            # 检查 job_id 是否存在
            cursor.execute("SELECT job_id FROM jobs WHERE job_id = %s", (job_id,))
            job = cursor.fetchone()

            if job is None:
                logging.warning(f"Job {job_id} not found. Cannot update.")
                return

            # 更新 job 的 status 和 result
            cursor.execute("UPDATE jobs SET status = %s, result = %s WHERE job_id = %s",
                           (status, result, job_id))

            # 追加新的 event 数据
            for event in event_data:
                cursor.execute("INSERT INTO events (job_id, timestamp, data) VALUES (%s, %s, %s)",
                               (job_id, datetime.now(), event))

            # 提交更改
            conn.commit()

            logging.info(f"Job {job_id} updated successfully.")

        except Error as e:
            logging.error(f"Error updating job {job_id}: {e}")
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()


# 定义函数 get_job_by_id，接受 job_id 作为参数，并返回 Job 对象
def get_job_by_id(job_id: str) -> Job:
    with jobs_lock:
        try:
            # 确保数据库连接有效
            conn = get_db_connection()
            if conn is None:
                raise Exception("Database connection is not available.")

            cursor = conn.cursor()

            # 从 jobs 表中检索作业的状态和结果
            cursor.execute("SELECT status, result FROM jobs WHERE job_id = %s", (job_id,))
            job_data = cursor.fetchone()

            if job_data is None:
                logging.warning(f"Job {job_id} not found.")
                return None

            # 从 events 表中检索与该作业相关的所有事件
            cursor.execute("SELECT timestamp, data FROM events WHERE job_id = %s", (job_id,))
            event_data = cursor.fetchall()

            # 将事件数据转换为 Event 对象的列表
            events = [Event(timestamp=row[0], data=row[1]) for row in event_data]

            # 创建并返回 Job 对象
            job = Job(status=job_data[0], events=events, result=job_data[1])
            return job

        except Error as e:
            logging.error(f"Error retrieving job {job_id}: {e}")
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()





