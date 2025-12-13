<?php
header('Content-Type: application/json');

// Only allow POST requests
if ($_SERVER["REQUEST_METHOD"] == "POST") {
    
    // 1. Sanitize and Collect Input
    $name = strip_tags(trim($_POST["name"]));
    $business = strip_tags(trim($_POST["business_name"]));
    $phone = strip_tags(trim($_POST["phone"]));
    $email = filter_var(trim($_POST["email"]), FILTER_SANITIZE_EMAIL);
    $message = strip_tags(trim($_POST["message"]));

    // 2. Validate Required Fields
    if (empty($name) || empty($phone) || empty($email) || !filter_var($email, FILTER_VALIDATE_EMAIL)) {
        http_response_code(400);
        echo json_encode(["message" => "Please complete all required fields correctly."]);
        exit;
    }

    // 3. Email Configuration
    $to = "admin@allwebbedup.com.au";
    $subject = "New Strategy Call Request - " . $name;
    
    // 4. Construct HTML Email Body (Brand UI)
    $email_content = "
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: 'Poppins', Arial, sans-serif; line-height: 1.6; color: #333; background-color: #f4fcf6; margin: 0; padding: 20px; }
            .email-container { max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
            .header { background-color: #00C647; color: #ffffff; padding: 20px; text-align: center; }
            .header h2 { margin: 0; font-size: 24px; font-weight: 600; }
            .content { padding: 30px; }
            .row { margin-bottom: 15px; border-bottom: 1px solid #f0f0f0; padding-bottom: 15px; }
            .row:last-child { border-bottom: none; }
            .label { font-weight: bold; color: #00C647; font-size: 14px; text-transform: uppercase; margin-bottom: 5px; display: block; }
            .value { font-size: 16px; color: #333; }
            .footer { background-color: #32373c; color: #888; text-align: center; padding: 15px; font-size: 12px; }
        </style>
    </head>
    <body>
        <div class='email-container'>
            <div class='header'>
                <h2>New Website Lead</h2>
            </div>
            
            <div class='content'>
                <p style='margin-bottom: 25px;'>You have received a new request for a digital marketing strategy call.</p>
                
                <div class='row'>
                    <span class='label'>Full Name</span>
                    <div class='value'>$name</div>
                </div>
                
                <div class='row'>
                    <span class='label'>Business Name</span>
                    <div class='value'>$business</div>
                </div>

                <div class='row'>
                    <span class='label'>Phone Number</span>
                    <div class='value'><a href='tel:$phone' style='color:#333; text-decoration:none;'>$phone</a></div>
                </div>

                <div class='row'>
                    <span class='label'>Email Address</span>
                    <div class='value'><a href='mailto:$email' style='color:#333; text-decoration:none;'>$email</a></div>
                </div>

                <div class='row'>
                    <span class='label'>Message</span>
                    <div class='value'>" . nl2br($message) . "</div>
                </div>
            </div>

            <div class='footer'>
                Sent from All Webbed Up Landing Page
            </div>
        </div>
    </body>
    </html>
    ";

    // 5. Set Headers
    $headers = "MIME-Version: 1.0" . "\r\n";
    $headers .= "Content-type:text/html;charset=UTF-8" . "\r\n";
    
    // Ideally use a sender address from your own domain to prevent spam flagging
    $headers .= "From: Website Form <noreply@allwebbedup.com.au>" . "\r\n";
    $headers .= "Reply-To: $email" . "\r\n";

    // 6. Send Email
    if (mail($to, $subject, $email_content, $headers)) {
        http_response_code(200);
        echo json_encode(["message" => "Email sent successfully"]);
    } else {
        http_response_code(500);
        echo json_encode(["message" => "Failed to send email."]);
    }

} else {
    // Not a POST request
    http_response_code(403);
    echo json_encode(["message" => "Access denied"]);
}
?>