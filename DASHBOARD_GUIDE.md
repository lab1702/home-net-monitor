# Dashboard Symbols Guide

## Overall System Status Header

The dashboard header dynamically shows the overall system health:

| Icon | Status | Description |
|------|--------|-------------|
| 🟢 | **All Systems Operational** | All monitored sites are online |
| 🟡 | **Partial Outage** | Some sites are down, but not all |
| 🔴 | **System Outage** | All monitored sites are down |
| ⚪ | **No Data Available** | No monitoring data found |

## Individual Site Status Indicators

The dashboard uses clear symbols to indicate the status of HTTP and ping tests for each monitored site.

### Symbol Legend

| Symbol | Meaning | Description |
|--------|---------|-------------|
| ✅ | **Success** | Test passed successfully |
| ❌ | **Failed** | Test was attempted but failed |
| ➖ | **Skipped** | Test was not performed (configured to skip) |

### Example Dashboard Display

```
🟢 Current Status - All Systems Operational

Site Status Details: (sorted alphabetically)
┌─────────────────────┬─────────┬──────┬──────┬─────────────────┐
│ Site                │ Status  │ HTTP │ Ping │ HTTP Response   │
├─────────────────────┼─────────┼──────┼──────┼─────────────────┤
│ Amazon              │ 🟢 Online│ ✅   │ ✅   │ 79.4ms          │
│ Cloudflare          │ 🟢 Online│ ✅   │ ✅   │ 346.4ms         │
│ GitHub              │ 🟢 Online│ ✅   │ ✅   │ 138.0ms         │
│ Google              │ 🟢 Online│ ✅   │ ✅   │ 98.1ms          │
│ Google DNS Secondary│ 🟢 Online│ ➖   │ ✅   │ N/A             │
│ Microsoft           │ 🟢 Online│ ✅   │ ➖   │ 234.4ms         │
│ Netflix             │ 🟢 Online│ ✅   │ ➖   │ 752.0ms         │
└─────────────────────┴─────────┴──────┴──────┴─────────────────┘
```

### Interpretation

#### Full Monitoring (HTTP + Ping)
- **Google**: `HTTP=✅, Ping=✅` - Both tests successful
- **GitHub**: `HTTP=✅, Ping=✅` - Both tests successful

#### HTTP-Only Monitoring  
- **Microsoft**: `HTTP=✅, Ping=➖` - HTTP works, ping skipped
- **Netflix**: `HTTP=✅, Ping=➖` - HTTP works, ping skipped

#### Ping-Only Monitoring
- **Google DNS Secondary**: `HTTP=➖, Ping=✅` - Ping works, HTTP skipped

#### Failure Cases (Examples)
- **Down Site**: `HTTP=❌, Ping=❌` - Both tests failed
- **HTTP Down**: `HTTP=❌, Ping=✅` - HTTP failed, ping successful
- **Ping Blocked**: `HTTP=✅, Ping=❌` - HTTP works, ping blocked

## Summary Statistics

The dashboard also shows summary statistics with proper handling of skipped tests:

### HTTP Response Times
- Shows average response times for sites with HTTP monitoring
- Displays "N/A" for ping-only sites

### Ping Times  
- Shows average ping times for sites with ping monitoring
- Displays "N/A" for HTTP-only sites

### Uptime Calculation
- Based on the overall_success field
- Site is considered "up" if ANY enabled test passes
- 100% uptime means all enabled tests have been passing

## Current System Status

With the current configuration:

**Full Monitoring (4 sites):**
- All show ✅ for both HTTP and Ping

**HTTP-Only (2 sites):**  
- Microsoft & Netflix show ✅ for HTTP, ➖ for Ping

**Ping-Only (1 site):**
- Google DNS Secondary shows ➖ for HTTP, ✅ for Ping

**Result:** 7/7 sites online (100% uptime)
