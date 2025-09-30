# User Guide: Creating an Account

## 🔐 How to Create Your Account

Since our application uses AWS Cognito with email alias configuration, you'll need to provide both a username and email address during signup.

### ✅ Step-by-Step Instructions:

#### 1. **Username Field**
- Enter a unique username (letters and numbers only)
- **Examples**: `john_doe`, `sarah123`, `mike_smith`
- **Cannot use**: Email format (no @ symbols)
- **Requirements**: Must be unique across all users

#### 2. **Email Address Field**  
- Enter your actual email address
- **Example**: `john.doe@company.com`
- **Used for**: Sign-in, notifications, password recovery

#### 3. **Password Field**
- Must meet security requirements:
  - At least 8 characters
  - Include uppercase letter
  - Include lowercase letter  
  - Include numbers
  - Special characters optional

### 🎯 Sign In Process (After Account Creation):

Once your account is created, you can sign in using:
- **Email Address**: Your email (not the username)
- **Password**: Your chosen password

### 💡 Why Both Username and Email?

This configuration provides:
- **Security**: Separate username for internal identification
- **Convenience**: Email-based sign-in
- **Flexibility**: Username privacy while using email for communication

### 🚨 Common Issues:

**"Username cannot be of email format"**
- ✅ **Solution**: Use a simple username like `john123` (not `john@email.com`)

**"Email already exists"**  
- ✅ **Solution**: Use a different email address or try signing in

### 📱 Mobile-Friendly Design:

The authentication interface works perfectly on:
- Desktop computers
- Tablets
- Mobile phones
- All modern browsers

### 🎨 Eventual Branding:

The interface features:
- Eventual's signature purple color (`#6a37b0`)
- Professional, centered layout
- Consistent branding throughout
- Accessible design elements

### 🔄 Password Recovery:

If you forget your password:
1. Click "Forgot your password?" on the sign-in page
2. Enter your email address
3. Check your email for reset instructions
4. Create a new password

This setup ensures both security and ease of use while maintaining compatibility with AWS Cognito's robust authentication system.