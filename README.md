# django-cache-decorator

## Overview
The `cache_result` decorator provides a way to cache function results in Django using the **Django cache framework** (e.g., Redis, Memcached). This can improve performance by reducing unnecessary database queries or API calls.

## Features
- Supports **Django's cache backend** (Redis, Memcached, etc.)
- Allows **custom cache expiration time**
- Supports **conditional caching** via `cache_filter`
- Generates **unique cache keys** based on function arguments

---

## Installation
Ensure Django's cache framework is properly configured in `settings.py`:

```python
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
    }
}
```

---
### **Basic Example**

```python
from django.core.cache import caches
from my_cache_decorator import cache_result

@cache_result(seconds=900)  # Cache results for 15 minutes
def get_data():
    print("Fetching data...")
    return {"message": "Hello, World!"}

# First call (not cached)
print(get_data())  # Output: Fetching data... {"message": "Hello, World!"}

# Second call (cached)
print(get_data())  # Output: {"message": "Hello, World!"} (No "Fetching data" printed)
```

---

## **Using `cache_filter` to Avoid Caching Invalid Data**

Sometimes, we want to **avoid caching** invalid results (e.g., `None`, empty lists, or errors).

### **Example: Avoid Caching `None` Results**
```python
@cache_result(seconds=600, cache_filter=lambda x: x is not None)
def get_user_data(user_id):
    print(f"Fetching user {user_id} from DB...")
    return User.objects.filter(id=user_id).first()  # Returns None if user doesn't exist

print(get_user_data(1))  # Calls DB and caches result
print(get_user_data(2))  # Calls DB but does NOT cache if user doesn't exist
```

---

## **Example: Caching a Database Query**

Let's cache a **database query** to avoid repeated queries for the same user.

```python
from django.db import models

class User(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)

@cache_result(cache_kwarg_keys=["user_id"], seconds=600)
def get_user(user_id):
    print(f"Fetching user {user_id} from database...")
    return User.objects.filter(id=user_id).values("id", "name", "email").first()

# First call (DB hit)
print(get_user(1))  # Fetches from DB and caches result

# Second call (Cache hit)
print(get_user(1))  # Returns cached result, no DB query
```

---

## **How It Works**
1. The decorator generates a **cache key** based on function arguments.
2. It checks if the **result exists in cache**:
   - ✅ If **found**, return cached result (fast ✅).
   - ❌ If **not found**, execute the function, store result in cache.
3. Optionally, **filters out unwanted results** using `cache_filter`.

---

## **Advanced: Custom Cache Setup**

You can specify a custom Django cache backend (e.g., separate Redis instance):

```python
@cache_result(seconds=300, cache_setup="secondary_cache")
def fetch_data():
    return expensive_computation()
```

Ensure `secondary_cache` is defined in `settings.py`:
```python
CACHES["secondary_cache"] = {
    "BACKEND": "django.core.cache.backends.redis.RedisCache",
    "LOCATION": "redis://127.0.0.1:6380/1",
}
```
---


