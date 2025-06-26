# LabVIEW Modifications for Dual PSU Control

Looking at your LabVIEW block diagram, I can see you have a good foundation for controlling a single PSU. Here are the specific modifications needed to support both PSUs:

## Key Issues in Current Implementation:

### 1. **Hard-coded PSU Type**
Your URLs are hard-coded to `/psu/1/` which appears to be FUG PSU only. You need to make this configurable.

### 2. **Missing PSU Selection**
You need a way to select which PSU (Heinzinger or FUG) to control.

### 3. **URL Structure Mismatch**
Your current URLs use `/psu/1/` but the service expects `/heinzinger/` or `/fug/`.

## Required Modifications:

### 1. **Add PSU Type Selection**
Add an **Enum Control** on the front panel:
```
PSU Type: [Heinzinger] [FUG]  (Ring/Enum control)
```

### 2. **Fix URL Building Logic**
Replace your hard-coded URLs with dynamic URL building:

**Current URLs in your diagram:**
- `http://192.168.88.2:5000/psu/1/set_current`
- `http://192.168.88.2:5000/psu/1/set_voltage` 
- `http://192.168.88.2:5000/psu/1/read`
- `http://192.168.88.2:5000/psu/1/relay`

**Should become:**
- `http://192.168.88.2:5001/heinzinger/set_current` (for Heinzinger)
- `http://192.168.88.2:5001/fug/set_current` (for FUG)
- etc.

### 3. **URL Building Block Diagram Changes**

**Add before each HTTP request:**
```
[PSU Type Enum] → [Case Structure]
  Case "Heinzinger": Output = "heinzinger"
  Case "FUG": Output = "fug"
[PSU String] → [Concatenate Strings] → [HTTP Client]
```

**New URL building logic:**
```
Base URL: "http://192.168.88.2:5001/"
PSU Type: "heinzinger" or "fug"
Endpoint: "set_voltage", "set_current", "read", "relay"
Final URL: Base + PSU Type + "/" + Endpoint
```

### 4. **Add Input Validation**

**Before each set operation, add validation:**
```
[PSU Type] → [Case Structure]
  Heinzinger Case:
    Voltage: 0 ≤ V ≤ 30000
    Current: 0 ≤ I ≤ 2.0
  FUG Case:
    Voltage: 0 ≤ V ≤ 50000  
    Current: 0 ≤ I ≤ 0.5
```

### 5. **Modify Relay Control Logic**

**Add logic to handle Heinzinger's lack of relay control:**
```
[PSU Type] → [Case Structure]
  Heinzinger Case: 
    Display error: "Heinzinger has no relay control"
    Disable relay controls
  FUG Case:
    Enable relay controls
    Send relay commands normally
```

### 6. **Update Port Number**
Change from port `5000` to `5001` to match the service.

### 7. **Enhanced Status Reading**

**Modify the read response parsing:**
```
JSON Response → [Case Structure based on PSU Type]
  Heinzinger Case:
    Parse: voltage, current
    Set relay status = false (always)
  FUG Case:
    Parse: voltage, current, "on" field
    Use actual relay status
```

## Suggested Block Diagram Structure:

### **Top Level - Add PSU Selection:**
```
┌─ Controls ─────────────────────────────────┐
│ PSU Type: [Heinzinger ▼] [FUG      ▼]     │
│ Voltage Setpoint: [_____] V                │
│ Current Setpoint: [_____] mA               │  
│ [Set Voltage] [Set Current] [Read Status]  │
│ Relay Control: [ON] [OFF] (enabled for FUG)│
└────────────────────────────────────────────┘
```

### **Block Diagram - URL Building:**
```
[PSU Type] → [Case Structure] → [PSU String]
                                      ↓
[Base URL] + [PSU String] + "/" + [Endpoint] → [Full URL]
                                      ↓
                              [HTTP Client Request]
```

### **Validation Logic:**
```
[Voltage Input] → [Case Structure - PSU Type]
  Heinzinger: [In Range 0-30000?] → [Enable/Disable Set Button]
  FUG:        [In Range 0-50000?] → [Enable/Disable Set Button]

[Current Input] → [Case Structure - PSU Type]  
  Heinzinger: [In Range 0-2.0?] → [Enable/Disable Set Button]
  FUG:        [In Range 0-0.5?] → [Enable/Disable Set Button]
```

## Quick Implementation Steps:

1. **Add PSU Type enum control** to front panel
2. **Replace all hard-coded URLs** with dynamic URL building using case structures
3. **Change port from 5000 to 5001**
4. **Add input validation** based on PSU type
5. **Handle relay control** differences between PSUs
6. **Update JSON parsing** to handle different response formats

This will give you a single LabVIEW VI that can control both PSUs safely with proper validation and error handling.