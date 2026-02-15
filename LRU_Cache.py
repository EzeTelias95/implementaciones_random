from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Dict, Generic, Hashable, Optional, TypeVar

K = TypeVar("K", bound=Hashable)
V = TypeVar("V")
F = TypeVar("F", bound=Callable[..., Any])

#Node roots
_SENTINEL = object()

@dataclass
class _Node(Generic[K,V]):
    key: K
    val: V
    prev: Optional["_Node[K,V]"] = None
    next: Optional["_Node[K,V]"] = None

class LRUCache():
    def __init__(self, capacity = 2):
        self._data: Dict[_Node[K,V]] = {}
        self._head: _Node[K,V] = _Node(key=_SENTINEL, val=_SENTINEL)
        self._tail: _Node[K,V] = _Node(key=_SENTINEL, val=_SENTINEL)
        self.capacity: int = capacity
        self._head.prev = self._tail
        self._tail.next = self._head
    
    def __len__(self):
        return len(self._data)
    
    def _move_front(self, node: _Node[K,V]):
        self._remove(node)
        
        prev_head = self._head.prev
        prev_head.next = node
        node.prev = prev_head  
        node.next = self._head
        self._head.prev = node
        
    def _remove(self, node: _Node[K,V]):
        prev = node.prev
        next = node.next
        
        if prev is not None:
            prev.next = next
            
        if next is not None:
            next.prev = prev
            
    def _pop(self):
        node = self._tail.next
        self._remove(node)
        return node
                
    def get(self, k: K, default: Optional[V] = None):
        node = self._data.get(k)
        if node is None:
            return default

        self._move_front(node)
        return node.val
        
    def put(self, k: K, v: V):
        node = self._data.get(k)
            
        if node is not None:            
            self._move_front(node)
            return node.val
        
        node = _Node(key=k, val=v)
        self._data[k] = node
        self._move_front(node)
        
        if len(self._data) > self.capacity:
            lru = self._pop()
            del self._data[lru.key]
            

@dataclass(frozen=True, slots=True)
class CacheInfo:
    hits: int
    misses: int
    max_size: int
    currsize: int

def _normalize_key(args, kwargs, typed): 
    if kwargs:
        items = tuple(sorted(kwargs.items()))
    else: 
        items = ()
        
    key = (args, items)
    
    if typed: 
        key = (args,items,tuple(type(a) for a in args),
                    tuple(type(v) for _,v in items))
    return key
        
def lru_cache_impl(max_size: int = 2, typed: bool= False)  -> Callable[[F], F]:
    
    if max_size  <= 0:
        raise ValueError("max_size must be > 0")
    
    def decorator(func: F):
        cache: LRUCache[Hashable, Any] = LRUCache(max_size)
        hits = 0 
        misses = 0
        
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            nonlocal hits, misses
            
            key= _normalize_key(args=args, kwargs=kwargs, typed=typed)
            cached = cache.get(key)
            if cached is not None:
                hits += 1
                return cached
            
            misses += 1
            value = func(*args, **kwargs)
            cache.put(key, value)
            return value
            

        def cache_info() -> CacheInfo:
            return CacheInfo(hits=hits, misses=misses, max_size=max_size, currsize=len(cache))

       

        setattr(wrapper, "cache_info", cache_info)
        return wrapper 
    
    return decorator
            