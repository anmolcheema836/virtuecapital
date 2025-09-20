<?php
if ( ! defined( 'ABSPATH' ) ) exit;

class HPI_Logger {

    private static $log_table = 'hpi_importer_logs';
    private $log_dir;

    public function __construct() {
        $upload_dir = wp_upload_dir();
        $this->log_dir = trailingslashit( $upload_dir['basedir'] ) . 'hpi-importer-logs';
        if ( ! is_dir( $this->log_dir ) ) {
            wp_mkdir_p( $this->log_dir );
        }
    }

    /**
     * Creates the custom log table in the database.
     */
    public static function create_log_table() {
        global $wpdb;
        $table_name = $wpdb->prefix . self::$log_table;
        $charset_collate = $wpdb->get_charset_collate();

        $sql = "CREATE TABLE $table_name (
            run_id BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
            start_time DATETIME NOT NULL,
            end_time DATETIME DEFAULT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'processing',
            source_file VARCHAR(255) NOT NULL,
            total_rows INT UNSIGNED NOT NULL DEFAULT 0,
            products_created INT UNSIGNED NOT NULL DEFAULT 0,
            products_updated INT UNSIGNED NOT NULL DEFAULT 0,
            products_skipped INT UNSIGNED NOT NULL DEFAULT 0,
            error_count INT UNSIGNED NOT NULL DEFAULT 0,
            log_file_path VARCHAR(255) DEFAULT NULL,
            PRIMARY KEY (run_id)
        ) $charset_collate;";

        require_once( ABSPATH . 'wp-admin/includes/upgrade.php' );
        dbDelta( $sql );
    }

    /**
     * Starts a new import run log entry.
     * @return int The ID of the new run log.
     */
    public function start_run( $file_path ) {
        global $wpdb;
        $table_name = $wpdb->prefix . self::$log_table;
        
        $log_file_name = 'run-' . date('Y-m-d-H-i-s') . '-' . wp_generate_password(8, false) . '.log';
        $log_file_path = trailingslashit($this->log_dir) . $log_file_name;

        $wpdb->insert(
            $table_name,
            [
                'start_time' => current_time( 'mysql' ),
                'status' => 'processing',
                'source_file' => basename( $file_path ),
                'log_file_path' => $log_file_path,
            ],
            [ '%s', '%s', '%s', '%s' ]
        );
        $run_id = $wpdb->insert_id;
        $this->log($run_id, "Import started for file: " . basename($file_path));
        return $run_id;
    }
    
    /**
     * Updates statistics for a run after a batch completes.
     */
    public function update_run_stats( int $run_id, array $stats ) {
        global $wpdb;
        $table_name = $wpdb->prefix . self::$log_table;
        
        $wpdb->query( $wpdb->prepare(
            "UPDATE $table_name 
            SET products_created = products_created + %d,
                products_updated = products_updated + %d,
                products_skipped = products_skipped + %d,
                error_count = error_count + %d
            WHERE run_id = %d",
            $stats['created'], $stats['updated'], $stats['skipped'], $stats['errors'], $run_id
        ));
    }
    
    public function update_run_meta(int $run_id, $meta_key, $meta_value) {
        global $wpdb;
        $table_name = $wpdb->prefix . self::$log_table;
        $wpdb->update($table_name, [$meta_key => $meta_value], ['run_id' => $run_id]);
    }

    /**
     * Marks a run as complete.
     */
    public function end_run( int $run_id, $status = 'completed' ) {
        global $wpdb;
        $table_name = $wpdb->prefix . self::$log_table;
        
        // Final check for errors to set status correctly
        $error_count = $wpdb->get_var($wpdb->prepare("SELECT error_count FROM $table_name WHERE run_id = %d", $run_id));
        if ($error_count > 0 && $status === 'completed') {
            $status = 'completed_with_errors';
        }

        $this->log($run_id, "Import finished with status: {$status}");
        $wpdb->update(
            $table_name,
            [ 'end_time' => current_time( 'mysql' ), 'status' => $status ],
            [ 'run_id' => $run_id ],
            [ '%s', '%s' ],
            [ '%d' ]
        );
    }
    
    /**
     * Appends a message to the detailed log file for a specific run.
     */
    public function log( int $run_id, string $message, string $level = 'info', array $context = [] ) {
        global $wpdb;
        $table_name = $wpdb->prefix . self::$log_table;
        $log_file = $wpdb->get_var($wpdb->prepare("SELECT log_file_path FROM $table_name WHERE run_id = %d", $run_id));

        if (!$log_file) return;

        $formatted_message = sprintf(
            "[%s] [%s]: %s\n",
            date('Y-m-d H:i:s'),
            strtoupper($level),
            $message
        );

        if (!empty($context)) {
            $formatted_message .= "CONTEXT: " . print_r($context, true) . "\n";
        }

        file_put_contents( $log_file, $formatted_message, FILE_APPEND );
    }
    
    /**
     * Sends an email notification summarizing the import run.
     */
    public function send_notification(int $run_id) {
        global $wpdb;
        $table_name = $wpdb->prefix . self::$log_table;
        $run_data = $wpdb->get_row($wpdb->prepare("SELECT * FROM $table_name WHERE run_id = %d", $run_id), ARRAY_A);

        if (!$run_data) return;

        $to = get_option('admin_email');
        $subject = sprintf("WooCommerce Product Import Complete: %s", $run_data['status']);
        
        $body  = "A product import has just finished.\n\n";
        $body .= "Status: " . strtoupper($run_data['status']) . "\n";
        $body .= "Source File: " . $run_data['source_file'] . "\n";
        $body .= "Start Time: " . $run_data['start_time'] . "\n";
        $body .= "End Time: " . $run_data['end_time'] . "\n";
        $body .= "-------------------------------------\n";
        $body .= "Total Rows in File: " . $run_data['total_rows'] . "\n";
        $body .= "Products Created: " . $run_data['products_created'] . "\n";
        $body .= "Products Updated: " . $run_data['products_updated'] . "\n";
        $body .= "Rows Skipped: " . $run_data['products_skipped'] . "\n";
        $body .= "Errors: " . $run_data['error_count'] . "\n";
        $body .= "-------------------------------------\n\n";
        
        if ($run_data['error_count'] > 0) {
            $body .= "Please review the detailed log file for error details.\n";
            // In a real scenario, you might provide a link to download the log.
        }

        wp_mail($to, $subject, $body);
    }
}