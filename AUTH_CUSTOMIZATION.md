# Authentication UI Customization

## 🎨 Overview

The agent2_ingestor application features a custom-branded authentication experience with Eventual's design system and simplified user flows.

## ✅ Current Implementation

### 🎯 Design & Branding
- **Primary Color**: Eventual's brand color `#6a37b0`
- **Centered Layout**: Authentication form centered on page with professional styling
- **Card Design**: Clean white card with subtle shadow and rounded corners
- **Responsive**: Optimized for all screen sizes

### 🖌️ Visual Elements Styled
- **Active Tab Highlighting**: Uses `#6a37b0` for active tab indicator and text
- **Primary Buttons**: Sign In and Create Account buttons use Eventual branding
- **Links**: "Forgot your password?" link styled with brand color
- **Form Focus**: Input fields show brand color focus states
- **Hover Effects**: Interactive elements have branded hover states

### 📝 Form Configuration
```typescript
const formFields = {
  signIn: {
    username: {
      placeholder: 'Enter your email address',
      label: 'Email Address',
    }
  },
  signUp: {
    username: {
      placeholder: 'Enter your email address',
      label: 'Email Address',
    }
  }
};
```

### 🎨 Custom Styling
```css
.amplify-authenticator {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f5f5f5;
}

.amplify-tabs__item[data-state="active"] {
  color: #6a37b0 !important;
  border-bottom-color: #6a37b0 !important;
}

.amplify-button[data-variation="primary"] {
  background-color: #6a37b0 !important;
  border-color: #6a37b0 !important;
}
```

## 🎯 User Experience

### Sign In Process:
1. **Centered Form**: Professional, centered authentication interface
2. **Email-Focused**: Clear "Email Address" labeling (no username confusion)
3. **Brand Consistency**: Eventual's purple branding throughout
4. **Password Recovery**: Branded "Forgot your password?" link

### Create Account Process:
1. **Simplified Fields**: Email and password (leverages Cognito email alias)
2. **Clear Labeling**: "Email Address" field guidance
3. **Password Requirements**: Standard Cognito password policy
4. **Verification**: Email-based account verification

## 📱 Mobile Optimization

The authentication interface is fully responsive:
- **Mobile Layout**: Stack elements vertically on small screens
- **Touch Targets**: Appropriately sized buttons for touch interaction
- **Font Scaling**: Readable text across device sizes
- **Form Spacing**: Comfortable padding and margins

## 🔧 Technical Implementation

### Theme Integration:
- Uses Material-UI theme with Eventual's primary color
- Overrides Amplify UI styles with custom CSS
- Maintains accessibility standards
- Consistent with application's overall design

### Cognito Integration:
- Email alias configuration for user-friendly sign-in
- Secure password requirements
- Email verification workflow
- Password reset functionality

## 🚀 Benefits

1. **Professional Branding**: Consistent with Eventual's visual identity
2. **Simplified UX**: Streamlined email-focused authentication
3. **Mobile-Friendly**: Works perfectly on all devices
4. **Accessible**: Meets accessibility standards
5. **Secure**: Leverages AWS Cognito security best practices

## 🎨 Color Palette

- **Primary**: `#6a37b0` (Eventual Purple)
- **Primary Hover**: `#5a2d96` (Darker Purple)
- **Background**: `#f5f5f5` (Light Gray)
- **Card**: `#ffffff` (White)
- **Text**: Standard Amplify UI text colors

This creates a cohesive, professional authentication experience that aligns with Eventual's brand while providing an intuitive user interface.

## 🚀 Deployment Status

- ✅ **DEV**: Updated and deployed (https://dev.dn1hdu83qdv9u.amplifyapp.com)
- 📋 **Next**: Deploy to TEST and MAIN environments when ready

## 🔧 Additional Customization Options

The Amplify Authenticator supports many other customizations:

### Password Requirements Display:
```typescript
formFields: {
  signUp: {
    password: {
      label: 'Password',
      placeholder: 'Enter your password',
      isRequired: true,
    }
  }
}
```

### Custom Validation Messages:
```typescript
formFields: {
  signUp: {
    email: {
      label: 'Email Address',
      placeholder: 'Enter your email',
      isRequired: true,
      order: 1
    }
  }
}
```

### Form Field Ordering:
Add `order` property to control field sequence.

## 📝 Notes

- The underlying Cognito configuration still uses email as the username attribute
- This customization only affects the UI labels and placeholders
- The form validation and authentication logic remain unchanged