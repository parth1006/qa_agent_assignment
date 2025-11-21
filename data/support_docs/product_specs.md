# E-Shop Checkout - Product Specifications

## Document Version
- **Version**: 1.0
- **Last Updated**: November 2024
- **Document Type**: Feature Specifications

---

## 1. Product Catalog

### 1.1 Available Products
The e-shop checkout system supports three products at launch:

| Product ID | Product Name | Price | Description |
|------------|--------------|-------|-------------|
| prod-001 | Wireless Headphones | $79.99 | High-quality Bluetooth headphones with noise cancellation |
| prod-002 | Smart Watch | $199.99 | Fitness tracking smartwatch with heart rate monitor |
| prod-003 | Portable Charger | $29.99 | 10000mAh portable power bank with fast charging |

### 1.2 Product Availability Rules
- All products are available for immediate purchase
- No inventory limits applied in current version
- Minimum quantity per item: 1
- Maximum quantity per item: 99

---

## 2. Shopping Cart Features

### 2.1 Cart Operations
- **Add to Cart**: Users can add products by clicking the "Add to Cart" button
- **Update Quantity**: Users can modify item quantities using the quantity input field
- **Remove Items**: Users can remove items using the "Remove" button
- **Empty Cart State**: When cart is empty, display message "Your cart is empty. Add some products!"

### 2.2 Cart Calculations
- **Subtotal**: Sum of (price × quantity) for all items in cart
- **Discount**: Applied as percentage reduction to subtotal
- **Shipping Cost**: Added to (Subtotal - Discount)
- **Total**: (Subtotal - Discount) + Shipping Cost

---

## 3. Discount Code System

### 3.1 Valid Discount Codes

#### SAVE15
- **Type**: Percentage Discount
- **Value**: 15% off subtotal
- **Conditions**: 
  - No minimum purchase required
  - Applies to entire cart subtotal
  - Cannot be combined with other offers
- **Calculation**: Discount Amount = Subtotal × 0.15

### 3.2 Invalid Discount Code Behavior
- If user enters an empty code, display: "✗ Please enter a discount code"
- If user enters an invalid code, display: "✗ Invalid discount code"
- Invalid codes should NOT apply any discount
- Previous discount should be removed when invalid code is applied

### 3.3 Valid Discount Code Behavior
- Display success message: "✓ Discount code applied! You saved 15%"
- Update cart summary to show discount amount
- Recalculate total price with discount applied
- Discount amount shown as negative value (e.g., -$12.00)

---

## 4. Shipping Methods

### 4.1 Standard Shipping
- **Cost**: Free ($0.00)
- **Delivery Time**: 5-7 business days
- **Description**: "Free - Delivery in 5-7 business days"
- **Default**: Standard shipping is selected by default

### 4.2 Express Shipping
- **Cost**: $10.00
- **Delivery Time**: 1-2 business days
- **Description**: "$10.00 - Delivery in 1-2 business days"
- **Calculation**: Fixed $10.00 added to total when selected

### 4.3 Shipping Calculation Rules
- Shipping cost is added AFTER discount is applied
- Formula: Total = (Subtotal - Discount) + Shipping
- Shipping selection is mandatory (default: Standard)

---

## 5. Payment Methods

### 5.1 Supported Payment Options

#### Credit Card
- **Default**: Selected by default
- **Description**: "Pay securely with your credit card"
- **Processing**: Client-side validation only (no actual payment processing)

#### PayPal
- **Description**: "Fast and secure PayPal checkout"
- **Processing**: Client-side validation only (no actual payment processing)

### 5.2 Payment Processing Rules
- Payment method selection is mandatory
- No actual payment gateway integration in current version
- Payment simulation triggers "Payment Successful!" message upon valid form submission

---

## 6. User Details Form

### 6.1 Required Fields

#### Full Name
- **Field ID**: user-name
- **Validation**: Cannot be empty
- **Error Message**: "Please enter your full name"
- **Format**: Text input, no special character restrictions

#### Email Address
- **Field ID**: user-email
- **Validation**: Must match standard email format (contains @ and domain)
- **Error Message**: "Please enter a valid email address"
- **Regex Pattern**: `/^[^\s@]+@[^\s@]+\.[^\s@]+$/`

#### Shipping Address
- **Field ID**: user-address
- **Validation**: Cannot be empty
- **Error Message**: "Please enter your shipping address"
- **Format**: Textarea, multiline input allowed

### 6.2 Form Validation Rules
- All three fields are mandatory
- Validation triggers on "Pay Now" button click
- Invalid fields display inline error messages in red text
- Invalid fields have red border highlighting
- Form submission is blocked if any validation fails
- Empty cart also blocks form submission with alert: "Your cart is empty. Please add items before checkout."

---

## 7. Order Processing

### 7.1 Successful Order Flow
1. User clicks "Pay Now" button
2. System validates all form fields
3. System checks cart is not empty
4. If all validations pass:
   - Display modal with "Payment Successful!" message
   - Show success checkmark icon (✓)
   - Display final order total
   - Provide "Close" button to dismiss modal

### 7.2 Order Completion Actions
- After closing success modal, reset the form:
  - Clear cart (empty all items)
  - Reset discount code application
  - Clear all form fields
  - Return shipping method to Standard (default)
  - Return payment method to Credit Card (default)

---

## 8. Business Rules Summary

### 8.1 Price Calculation Order
1. Calculate Subtotal from cart items
2. Apply Discount (if valid code entered)
3. Add Shipping Cost
4. Display Total

### 8.2 Validation Hierarchy
1. Check cart is not empty
2. Validate user name (not empty)
3. Validate email (proper format)
4. Validate address (not empty)
5. Check shipping method selected
6. Check payment method selected

### 8.3 Feature Dependencies
- Discount code can only be applied if cart has items
- Shipping cost affects total only after discount
- Form submission requires both cart items AND valid user details
- Payment success modal only displays after all validations pass

---

## 9. Future Enhancements (Not Implemented)
- Multiple discount codes support
- Tiered shipping rates based on weight/location
- Real payment gateway integration
- Order tracking system
- User account management
- Saved addresses
- Multiple shipping addresses

---

## Document Notes
This specification document serves as the authoritative source for all feature requirements and business logic of the E-Shop Checkout system. All test cases should be grounded in these specifications.
