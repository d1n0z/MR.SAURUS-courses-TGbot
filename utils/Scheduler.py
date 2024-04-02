import asyncio
import heapq
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import partial
from typing import Awaitable, Any, Union, List, Optional, Tuple
from uuid import UUID, uuid4


@dataclass
class Task:
    priority: Union[int, datetime]
    uuid: UUID
    callback: Awaitable[Any]


class Scheduler:

    def __init__(self, max_tasks: Optional[int] = None):
        self.tasks: List[Task] = []
        self.task: Optional[asyncio.Task[None]] = None
        self.task_count = 0
        self.running: List[Tuple[Task, asyncio.Task[Any]]] = []
        self.next: Optional[Task] = None
        self.added = asyncio.Event()
        self.restart = asyncio.Event()
        self.max_tasks = max_tasks

    def start(self):
        self.task = asyncio.create_task(self.loop())

    async def loop(self):
        while True:
            if self.next is None:
                print("waiting task")
                await self.added.wait()
                print("awaited")
            next_ = self.next
            assert next_ is not None and isinstance(
                next_.priority, datetime
            )

            print(f"starting in {next_.priority - datetime.now()}")

            done, _ = await asyncio.wait(  # NOQA
                [await asyncio.sleep((next_.priority - datetime.now()).total_seconds()),  # NOQA
                 await self.restart.wait(), ], return_when=asyncio.FIRST_COMPLETED, )  # NOQA
            print(f"waiting is done")

            fut = done.pop()
            print("popped")
            if fut.result() is True:
                print("next")
                continue

            task = asyncio.create_task(next_.callback)
            print("task created")
            self.running.append((next_, task))
            task.add_done_callback(partial(self.callback, task_obj=next_))

            try:
                self.next = heapq.heappop(self.tasks)
                self.task_count -= 1
            except IndexError:
                self.next = None
                self.task_count = 0

    def callback(self, task_obj: Task) -> None:
        for idx, (running_task, _) in enumerate(self.running):
            if running_task.uuid == task_obj.uuid:
                del self.running[idx]  # NOQA

    def cancel(self, task: Task) -> bool:
        if self.next is not None and task.uuid == self.next.uuid:
            if self.tasks:
                self.next = heapq.heappop(self.tasks)
            else:
                self.next = None
            self.task_count -= 1
            self.restart.set()
            self.restart.clear()
            return True

        for idx, (running_task, asyncio_task) in enumerate(self.running):
            if running_task.uuid == task.uuid:
                del self.running[idx]  # NOQA
                asyncio_task.cancel()
                return True

        for idx, scheduled_task in enumerate(self.tasks):
            if scheduled_task.uuid == task.uuid:
                del self.tasks[idx]
                self.task_count -= 1
                heapq.heapify(self.tasks)
                return True

        return False

    def schedule(self, coro: Awaitable[Any], when: datetime = datetime.now(), delay: int = 0) -> Task:
        if self.max_tasks is not None and self.task_count >= self.max_tasks:
            raise ValueError(f"Maximum tasks of {self.max_tasks} reached")

        when += timedelta(seconds=delay + 1.1)
        if when < datetime.now():
            raise ValueError("May only be in the future.")

        self.task_count += 1
        task = Task(priority=when, uuid=uuid4(), callback=coro)

        if self.next:
            assert isinstance(self.next.priority, datetime)
            if when < self.next.priority:
                heapq.heappush(self.tasks, self.next)
                self.next = task
                self.restart.set()
                self.restart.clear()
            else:
                heapq.heappush(self.tasks, task)
        else:
            self.next = task
            self.added.set()
            self.added.clear()

        return task


def s(text: str):
    print(text)


async def main():
    z = Scheduler()
    z.start()
    s("started")
    time.sleep(1)
    v = s("test")  # NOQA
    z.schedule(v)  # NOQA
    z.schedule(lambda: print("xd"))  # NOQA
    # z.schedule(lambda: s("xad"), delay=1)
    while True:
        time.sleep(0.1)


if __name__ == "__main__":
    asyncio.run(main())
