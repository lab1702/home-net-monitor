# Site Configuration Guide

## Overview

The network monitor supports three types of monitoring configurations:

1. **Full Monitoring** (HTTP + Ping) - Default
2. **HTTP-Only Monitoring** (Skip Ping)
3. **Ping-Only Monitoring** (Skip HTTP)

## How to Configure Sites to Monitor

Sites are configured in the `config.py` file in the `MONITOR_SITES` list.

### Basic Configuration

Each site requires these fields:

```python
{
    "name": "Display Name",           # Name shown in dashboard (required)
    "url": "https://example.com",     # URL for HTTP checks (required)
    "ping_host": "example.com"        # Host/IP for ping checks (optional)
}
```

### Configuration Validation

**Required Fields:**
- `name`: Display name (always required)
- At least one of `url` or `ping_host` must be specified

**Optional Fields:**
- `url`: HTTP endpoint (optional if ping_host specified)
- `ping_host`: Ping target (optional if url specified)

## Monitoring Types

### 1. Full Monitoring (HTTP + Ping)
Monitor both HTTP response and network connectivity.

```python
{
    "name": "Google",
    "url": "https://www.google.com",
    "ping_host": "8.8.8.8"
}
```

**Use for:** Most websites, web services, APIs with ping support
**Health Logic:** Site is healthy if **either** HTTP **or** ping works

### 2. HTTP-Only Monitoring
Skip ping tests for sites that block ICMP.

```python
{
    "name": "Microsoft", 
    "url": "https://www.microsoft.com",
    "ping_host": None  # Skip ping test
}
```

**Use for:**
- Websites that block ping (Microsoft, many CDNs)
- Load-balanced services
- API endpoints
- Services behind firewalls

**Health Logic:** Site is healthy if HTTP works

**Multiple ways to configure HTTP-only:**
```python
# Method 1: Set ping_host to None (Recommended)
{"name": "Site", "url": "https://example.com", "ping_host": None}

# Method 2: Set ping_host to empty string
{"name": "Site", "url": "https://example.com", "ping_host": ""}

# Method 3: Set ping_host to False
{"name": "Site", "url": "https://example.com", "ping_host": False}

# Method 4: Omit ping_host entirely
{"name": "Site", "url": "https://example.com"}
```

### 3. Ping-Only Monitoring
Skip HTTP tests for services without web interfaces.

```python
{
    "name": "Google DNS",
    "ping_host": "8.8.8.8"
    # No 'url' field - skip HTTP test
}
```

**Use for:**
- DNS servers
- Mail servers
- Database servers
- Network equipment (switches, routers)
- Internal services without web interfaces

**Health Logic:** Site is healthy if ping works

## Configuration Examples

### Web Services

#### External Websites (Full Monitoring)
```python
{
    "name": "Google",
    "url": "https://www.google.com",
    "ping_host": "8.8.8.8"
},
{
    "name": "GitHub",
    "url": "https://www.github.com",
    "ping_host": "github.com"
},
{
    "name": "Cloudflare",
    "url": "https://www.cloudflare.com",
    "ping_host": "1.1.1.1"
}
```

#### Major Websites (HTTP-Only - Often Block Ping)
```python
{
    "name": "Microsoft",
    "url": "https://www.microsoft.com",
    "ping_host": None
},
{
    "name": "Netflix",
    "url": "https://www.netflix.com",
    "ping_host": None
},
{
    "name": "Facebook",
    "url": "https://www.facebook.com",
    "ping_host": None
},
{
    "name": "Twitter",
    "url": "https://www.twitter.com",
    "ping_host": None
}
```

#### APIs and Web Apps (HTTP-Only)
```python
{
    "name": "Weather API",
    "url": "https://api.openweathermap.org",
    "ping_host": None
},
{
    "name": "My App",
    "url": "https://myapp.example.com",
    "ping_host": None
}
```

### Infrastructure Services

#### DNS Servers (Ping-Only)
```python
{
    "name": "Google DNS Primary",
    "ping_host": "8.8.8.8"
},
{
    "name": "Google DNS Secondary",
    "ping_host": "8.8.4.4"
},
{
    "name": "Cloudflare DNS",
    "ping_host": "1.1.1.1"
},
{
    "name": "OpenDNS",
    "ping_host": "208.67.222.222"
}
```

#### Network Equipment (Ping-Only)
```python
{
    "name": "Home Router",
    "ping_host": "192.168.1.1"
},
{
    "name": "Core Switch",
    "ping_host": "10.0.1.2"
},
{
    "name": "Firewall",
    "ping_host": "10.0.1.1"
}
```

#### Servers (Ping-Only)
```python
{
    "name": "Mail Server",
    "ping_host": "mail.example.com"
},
{
    "name": "Database Server",
    "ping_host": "db.internal.com"
},
{
    "name": "File Server",
    "ping_host": "files.internal.com"
}
```

## Common Use Cases

### Monitor Internet Connectivity
```python
{
    "name": "Internet Check",
    "url": "https://www.google.com",
    "ping_host": "8.8.8.8"  # Google DNS
}
```

### Monitor Local Network
```python
{
    "name": "Router",
    "url": "http://192.168.1.1",
    "ping_host": "192.168.1.1"
}
```

### Monitor Streaming Services
```python
{
    "name": "YouTube",
    "url": "https://www.youtube.com",
    "ping_host": "youtube.com"
}
```

## Invalid Configurations

```python
# ❌ Invalid - no tests specified
{
    "name": "Invalid Site"
    # Missing both url and ping_host
}

# ❌ Invalid - both fields empty
{
    "name": "Invalid Site",
    "url": "",
    "ping_host": ""
}
```

## Monitoring Behavior

### Log Messages
```
# Full monitoring
INFO: Monitored Google: HTTP=True, Ping=True, Overall=True

# HTTP-only
INFO: Monitored Microsoft: HTTP=True, Ping=skipped, Overall=True

# Ping-only
INFO: Monitored DNS Server: HTTP=skipped, Ping=True, Overall=True
```

### Database Storage
- HTTP tests store: `http_success`, `http_status_code`, `http_response_time_ms`
- Ping tests store: `ping_success`, `ping_avg_ms`, `ping_packet_loss_percent`
- Skipped tests store: `NULL` values in database
- Overall result: `overall_success` (true if any enabled test passes)

## Benefits by Monitoring Type

### HTTP-Only Benefits
1. **No Failed Ping Warnings**: Cleaner logs without constant ping failure warnings
2. **Faster Monitoring**: Skips unnecessary ping attempts
3. **More Accurate**: Focus on what matters (HTTP availability)
4. **Reduced Network Traffic**: Less monitoring overhead

### Ping-Only Benefits
1. **Monitor Critical Infrastructure**: DNS servers, network equipment
2. **No Unnecessary HTTP Requests**: Focus on network connectivity
3. **Monitor Non-Web Services**: Mail servers, database servers
4. **Simple Network Reachability**: Pure connectivity testing

## Important Notes

1. **HTTPS vs HTTP**: Use HTTPS when available, HTTP for local devices
2. **Ping blocking**: Many sites block ping but allow HTTP - this is normal
3. **Health logic**: A site is considered healthy if ANY enabled test passes
4. **DNS servers**: IPs like 8.8.8.8, 1.1.1.1 are reliable for ping tests
5. **At least one test required**: Must specify either 'url' or 'ping_host' (or both)

## Current Configuration

The system currently monitors these sites:
- **Google** (full monitoring: HTTP + ping 8.8.8.8)
- **GitHub** (full monitoring: HTTP + ping)
- **Cloudflare** (full monitoring: HTTP + ping 1.1.1.1)
- **Amazon** (full monitoring: HTTP + ping)
- **Microsoft** (HTTP-only: ping skipped)
- **Netflix** (HTTP-only: ping skipped)
- **Google DNS Secondary** (ping-only: 8.8.4.4, no HTTP)

**Result:** 7/7 sites online with mixed monitoring types

## After Making Changes

1. **Edit** `config.py` and modify the `MONITOR_SITES` list
2. **Rebuild** containers: `docker compose build`
3. **Restart** services: `docker compose up -d`
4. **Verify** in logs: `docker logs home-net-monitor`

## Troubleshooting

- **Ping fails but HTTP works**: Normal for many websites
- **Both fail**: Check if the site is actually down or URL is correct
- **Local sites fail**: Verify IP addresses and network connectivity
- **Changes not applied**: Make sure to rebuild Docker containers

For more details, see the main README.md file.
