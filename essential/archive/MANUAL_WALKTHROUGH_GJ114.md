# GJ114 Manual Walkthrough - Login Flow Documentation

## Purpose
This document records the exact sequence of steps and page states during the GJ114 auto login process to understand what the script should expect at each stage.

---

## Login Flow Steps

### Step 1: Initial Page Load
**URL:** `https://sasstocko.broker.tradetron.tech/auth/{auth_code}`
**Expected Content:** Login form with two fields
- **Field 1:** Client ID (username field)
  - Attribute: `name="login_id"`
  - Type: Text input
  - Placeholder/Label: "Client ID" or "Username"
  
- **Field 2:** Password
  - Attribute: `name="password"`
  - Type: Password input
  - Placeholder/Label: "Password"

- **Submit Button:** Present with `type="submit"`

**Script Action:** 
```
[GJ114] ✓ Entered Client ID: GJ114
[GJ114] ✓ Entered password
[GJ114] ✓ Login form submitted
[GJ114] ⏳ Waiting for TOTP page...
```

---

### Step 2: After Login Form Submission
**Expected Action:** Page redirects/changes after login form is submitted

**Possible Outcomes:**
- ❓ Does page stay on same URL?
- ❓ Does URL change immediately?
- ❓ Is there a loading screen?
- ❓ How long does it take for TOTP page to appear?

**Current Issue:** TOTP field is NOT appearing after 10 seconds of waiting

**Debugging Output Needed:**
```
[GJ114] DEBUG: Page text length: ???
[GJ114] DEBUG: Page text: ???
[GJ114] DEBUG: Current URL: ???
```

---

### Step 3: TOTP Page (Expected but NOT FOUND)
**What We're Looking For:**
- TOTP input field with `name="answers[]"` OR `name="totp"` OR `id="totp"`
- A submit button to send the TOTP code
- Any text indicating "2FA", "TOTP", "OTP", "verification code"

**Expected Page Content:**
- Should have more than 100 characters of text
- Should contain words related to "code", "verify", "authenticate", "2FA", "OTP"

**Script Action (Expected):**
```
[GJ114] 📱 TOTP field found! Generating and entering code...
[GJ114] ✓ TOTP code entered: {6-digit-code}
[GJ114] ✓ TOTP form submitted
[GJ114] ⏳ Waiting for success page...
```

---

### Step 4: Success Page
**Expected Content:** Page that contains the word "success"
**Expected URL:** Final redirect URL after TOTP verification
**Expected Time:** Within 15 seconds of TOTP submission

**Script Action (Expected):**
```
[GJ114] ✓ Success page found!
[GJ114] ============================================================
[GJ114] ✓✓✓ LOGIN SUCCESSFUL! ✓✓✓
[GJ114] Full authentication process completed!
[GJ114] ============================================================
```

---

## Manual Testing Instructions

### To Complete This Walkthrough:

1. **Run the script in MANUAL MODE** (not automated mode)
   - Change `STOCKO_AUTO_MODE=false` in .env.GJ114
   - Run: `python essential/stocko_auto_login_GJ114.py`

2. **At the Login Form:**
   - Manually enter your Client ID
   - Manually enter your Password
   - Let the script monitor and proceed

3. **At the TOTP Page:**
   - When TOTP field appears, note the following:
     - [ ] Field name attribute (name="???" or id="???")
     - [ ] Field type (text, password, hidden, etc)
     - [ ] Any label or placeholder text
     - [ ] Any surrounding elements or divs
     - [ ] Full page URL at this stage
     - [ ] All text visible on the page

4. **At the Success Page:**
   - Note the following:
     - [ ] Exact text/message shown
     - [ ] Final URL after login
     - [ ] Page title
     - [ ] Any redirect behavior

---

## Information to Record

### Session 1: [DATE/TIME]
**Status:** ⏳ In Progress / ✅ Complete / ❌ Failed

**Login Form Page:**
- URL: 
- Fields Found: login_id ✅, password ✅
- Submit Button: ✅

**After Form Submission:**
- URL Changed To: 
- Page Text Length: 
- Page Contains: 
- Time to Load: 

**TOTP Field Status:**
- Field Found: YES / NO
- Field Name/ID: 
- Field Type: 
- Page URL at this stage: 
- Full Page Text:
```
[Paste page text here if field not found]
```

**Success Page:**
- Reached: YES / NO
- Success Text: 
- Final URL: 
- Time to Success: 

**Notes:**
```
[Add any observations or issues]
```

---

## Current Status

### Last Run Results:
- ❌ TOTP field NOT found
- 📊 Page text length: 47 characters (too short - page not fully loaded?)
- 🔗 URL stuck at: `https://api.stocko.in/oauth/login?login_challenge=...`

### Possible Issues:
1. TOTP page not loading - may need longer wait time
2. TOTP form might be on a different page/URL
3. TOTP field might use different HTML attribute names
4. Page might require additional interaction before TOTP appears
5. JavaScript might be required to render TOTP field

### Next Steps:
1. Run in MANUAL MODE to observe browser behavior
2. Document exact field names and page states
3. Check browser console for any errors
4. Verify if redirects are working properly
5. Update script based on actual page structure

---

## Update Log

### Version 1.0 - Initial Creation
- Created manual walkthrough template
- Identified TOTP field detection issue
- Prepared for manual testing phase
