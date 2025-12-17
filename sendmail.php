<?php
/**
 * All Webbed Up - Lead Handling Script
 * Handles form submissions and sends a branded HTML email.
 */

// 1. CONFIGURATION
// ------------------------------------------------
$to_email = "admin@allwebbedup.com.au"; 
$subject  = "🚀 New Lead: Strategy Call Request";


$from_email = "noreply@" . $_SERVER['HTTP_HOST']; 


// 2. CHECK REQUEST METHOD
// ------------------------------------------------
if ($_SERVER["REQUEST_METHOD"] == "POST") {

    // 3. SANITIZE & VALIDATE INPUTS
    // ------------------------------------------------
    $name = isset($_POST['name']) ? strip_tags(trim($_POST['name'])) : 'Not Provided';
    $business = isset($_POST['business_name']) ? strip_tags(trim($_POST['business_name'])) : 'Not Provided';
    $phone = isset($_POST['phone']) ? strip_tags(trim($_POST['phone'])) : 'Not Provided';
    $email = isset($_POST['email']) ? filter_var(trim($_POST['email']), FILTER_SANITIZE_EMAIL) : '';
    $message = isset($_POST['message']) ? strip_tags(trim($_POST['message'])) : 'No message provided.';

    // Basic validation
    if (empty($name) || empty($phone) || empty($email)) {
        http_response_code(400);
        echo json_encode(["message" => "Please fill in all required fields."]);
        exit;
    }

    
    $email_content = "
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');
            body { font-family: 'Poppins', Arial, sans-serif; background-color: #f4fcf6; margin: 0; padding: 0; }
            .container { max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 5px 15px rgba(0,0,0,0.05); margin-top: 30px; margin-bottom: 30px; }
            .header { background-color: #00280f; padding: 30px; text-align: center; }
            .header h1 { color: #ffffff; margin: 0; font-size: 24px; font-weight: 600; letter-spacing: 1px; }
            .accent-bar { height: 6px; background-color: #00C647; width: 100%; }
            .content { padding: 40px 30px; color: #333333; }
            .label { color: #888; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; font-weight: 600; }
            .value { font-size: 16px; font-weight: 400; color: #000; margin-bottom: 25px; border-bottom: 1px solid #f0f0f0; padding-bottom: 10px; }
            .highlight { color: #00C647; font-weight: 600; }
            .message-box { background-color: #f9f9f9; padding: 20px; border-radius: 8px; border-left: 4px solid #00C647; font-style: italic; }
            .footer { background-color: #f8f8f8; padding: 20px; text-align: center; font-size: 12px; color: #999; }
            .btn { display: inline-block; background-color: #00C647; color: #ffffff; text-decoration: none; padding: 12px 24px; border-radius: 50px; font-weight: 600; margin-top: 10px; }
        </style>
    </head>
    <body>
        <div class='container'>
            <div class='header'>
                <h1>All Webbed Up</h1>
            </div>
            <div class='accent-bar'></div>
            
            <div class='content'>
                <h2 style='margin-top:0; color:#00280f;'>New Strategy Call Request</h2>
                <p>You have received a new lead from the landing page. Here are the details:</p>
                <br>

                <div class='label'>Client Name</div>
                <div class='value'>$name</div>

                <div class='label'>Business Name</div>
                <div class='value'>$business</div>

                <div class='label'>Phone Number</div>
                <div class='value'>
                    <a href='tel:$phone' style='text-decoration:none; color:#333;'>$phone</a>
                </div>

                <div class='label'>Email Address</div>
                <div class='value'>
                    <a href='mailto:$email' style='text-decoration:none; color:#333;'>$email</a>
                </div>

                <div class='label'>Message / Goals</div>
                <div class='value message-box'>
                    \"$message\"
                </div>

                <div style='text-align: center; margin-top: 30px;'>
                    <a href='tel:$phone' class='btn'>Call Lead Now</a>
                    <a href='mailto:$email' class='btn' style='background-color: #333;'>Reply via Email</a>
                </div>
            </div>

            <div class='footer'>
                Received: " . date("F j, Y, g:i a") . "<br>
                Source: Website Landing Page Form
            </div>
        </div>
    </body>
    </html>
    ";

    // 5. SET HEADERS
    // ------------------------------------------------
    $headers  = "MIME-Version: 1.0" . "\r\n";
    $headers .= "Content-type:text/html;charset=UTF-8" . "\r\n";
    $headers .= "From: All Webbed Up Leads <$from_email>" . "\r\n";
    $headers .= "Reply-To: $name <$email>" . "\r\n"; // Clicking Reply replies to the customer

    // 6. SEND EMAIL
    // ------------------------------------------------
    if (mail($to_email, $subject, $email_content, $headers)) {
        // Success Response (JSON)
        http_response_code(200);
        echo json_encode(["status" => "success", "message" => "Email sent successfully."]);
    } else {
        // Failure Response (JSON)
        http_response_code(500);
        echo json_encode(["status" => "error", "message" => "Server failed to send email."]);
    }

} else {
    // Handle direct access to file
    http_response_code(403);
    echo "Access Forbidden";
}
?>