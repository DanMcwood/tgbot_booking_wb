import asyncio
from datetime import datetime

class MultiUserLimiter:
    def __init__(self, call_limit, time_frame):
        self.call_limit = call_limit
        self.time_frame = time_frame
        self.user_limiters = {}

    async def can_user_call(self, user_id):
        if user_id not in self.user_limiters:
            self.user_limiters[user_id] = AsyncCallLimiter(self.call_limit, self.time_frame)

        return await self.user_limiters[user_id].can_call()
    
class AsyncCallLimiter:
    def __init__(self, call_limit, time_frame):
        self.call_limit = call_limit
        self.time_frame = time_frame
        self.call_count = 0
        self.last_called = None
        self.lock = asyncio.Lock()

    async def can_call(self):
        async with self.lock:  
            now = datetime.now()

            # Если первый вызов или окно времени истекло
            if self.last_called is None or now - self.last_called > self.time_frame:
                self.last_called = now
                self.call_count = 1
                return True
            print(self.call_count)

            # Проверяем, сколько вызовов сделано в текущем окне времени
            if self.call_count < self.call_limit:
                self.call_count += 1
                print(self.call_count)
                return True

            # Лимит превышен
            return False