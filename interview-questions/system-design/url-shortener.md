# URL Shortener System Design

## Problem Statement
Design a URL shortening service like bit.ly or tinyurl.com that:
- Takes a long URL and returns a short URL
- Redirects short URLs to original long URLs
- Handles billions of URLs
- Provides analytics (optional)

## Requirements

### Functional Requirements
1. Given a URL, generate a shorter and unique alias
2. When users access short URL, redirect to original URL
3. Users can optionally pick custom short links
4. Links should expire after a default timespan (configurable)

### Non-Functional Requirements
1. High availability (system should be always up)
2. Low latency for redirection
3. Short links should not be predictable
4. Analytics: track number of redirects

### Extended Requirements
- REST API
- Analytics dashboard
- Rate limiting

## Capacity Estimation

### Traffic
- Assume 100:1 read/write ratio
- 500M new URLs per month
- Read requests: 50B per month
- QPS (write): 200 URLs/sec
- QPS (read): 20K redirects/sec

### Storage
- Each URL entry: ~500 bytes
- Total URLs over 5 years: 30B URLs
- Storage needed: 15TB

### Bandwidth
- Write: 100KB/sec
- Read: 10MB/sec

## System APIs

```
POST /api/v1/shorten
Body: {
  "longUrl": "https://example.com/very/long/url",
  "customAlias": "mylink",  // optional
  "expiration": "2024-12-31" // optional
}
Response: {
  "shortUrl": "https://short.ly/abc123",
  "longUrl": "https://example.com/very/long/url",
  "created": "2024-01-01T00:00:00Z"
}

GET /{shortCode}
Response: 302 Redirect to original URL
```

## Database Schema

```sql
-- URL mappings table
CREATE TABLE urls (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  short_code VARCHAR(10) UNIQUE NOT NULL,
  original_url VARCHAR(2048) NOT NULL,
  user_id BIGINT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  expires_at TIMESTAMP,
  clicks BIGINT DEFAULT 0,
  INDEX idx_short_code (short_code),
  INDEX idx_user_id (user_id)
);

-- Analytics table (optional)
CREATE TABLE analytics (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  short_code VARCHAR(10),
  timestamp TIMESTAMP,
  ip_address VARCHAR(45),
  user_agent TEXT,
  referrer VARCHAR(2048),
  INDEX idx_short_code_timestamp (short_code, timestamp)
);
```

## URL Shortening Algorithm

### Approach 1: Hash-based
1. Compute hash (MD5/SHA256) of original URL
2. Take first 6-8 characters
3. Handle collisions by appending counter

**Pros**: Fast, deterministic
**Cons**: Collision handling needed, predictable

### Approach 2: Base62 Encoding
1. Use auto-incrementing ID
2. Encode ID to Base62 (0-9, a-z, A-Z)
3. 6 characters = 62^6 ≈ 56B unique URLs

```python
def encode_base62(num):
    chars = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    if num == 0:
        return chars[0]
    
    result = []
    while num > 0:
        result.append(chars[num % 62])
        num //= 62
    return ''.join(reversed(result))

def decode_base62(string):
    chars = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    num = 0
    for char in string:
        num = num * 62 + chars.index(char)
    return num
```

**Pros**: Unique, short codes
**Cons**: Sequential, need distributed ID generation

### Approach 3: Random Generation
1. Generate random 6-8 character string
2. Check if exists in database
3. Retry if collision

**Pros**: Non-sequential, unpredictable
**Cons**: Need collision checking

## High-Level Design

```
                    ┌──────────────┐
                    │ Load Balancer│
                    └──────┬───────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
     ┌────▼─────┐    ┌────▼─────┐    ┌────▼─────┐
     │ App      │    │ App      │    │ App      │
     │ Server 1 │    │ Server 2 │    │ Server 3 │
     └────┬─────┘    └────┬─────┘    └────┬─────┘
          │                │                │
          └────────────────┼────────────────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
         ┌────▼─────┐ ┌───▼─────┐ ┌───▼─────┐
         │  Cache   │ │Database │ │Analytics│
         │  (Redis) │ │(MySQL)  │ │  (Kafka)│
         └──────────┘ └─────────┘ └─────────┘
```

## Key Components

### 1. Application Layer
- Handle URL shortening requests
- Validate URLs
- Generate short codes
- Redirect to original URLs

### 2. Database Layer
- Store URL mappings
- NoSQL (Cassandra/DynamoDB) for high write throughput
- Or partitioned SQL (MySQL with sharding)

### 3. Cache Layer (Redis)
- Cache popular URLs (80-20 rule)
- LRU eviction policy
- Reduce database load for reads

### 4. Analytics
- Async logging to message queue (Kafka)
- Process in batches
- Store in separate analytics DB

## Scaling Considerations

### Database Partitioning
- Partition by hash of short code
- Consistent hashing for distribution
- Replication for high availability

### Caching Strategy
- Cache hot URLs (20% URLs = 80% traffic)
- Write-through cache for new URLs
- TTL based on URL expiration

### Rate Limiting
- Per user/IP limits
- Token bucket algorithm
- Prevent abuse

## Security
- Validate URLs (prevent malicious sites)
- Rate limiting
- CAPTCHA for suspicious activity
- HTTPS only
- SQL injection prevention

## Monitoring
- Latency metrics
- Error rates
- Cache hit ratio
- Database query performance
- System resource utilization

## References
- [System Design Interview Vol. 1](https://www.amazon.com/System-Design-Interview-insiders-Second/dp/B08CMF2CQF)
- [Designing Data-Intensive Applications](https://dataintensive.net/)
