<?php
if ( ! defined( 'ABSPATH' ) ) exit;

class HPI_Admin {
    public function __construct() {
        add_action('wp_dashboard_setup', [$this, 'add_dashboard_widget']);
    }

    public function add_dashboard_widget() {
        wp_add_dashboard_widget(
            'hpi_importer_status_widget',
            'High-Performance Importer Status',
            [$this, 'render_dashboard_widget']
        );
    }

    public function render_dashboard_widget() {
        global $wpdb;
        $table_name = $wpdb->prefix . 'hpi_importer_logs';
        
        if ($wpdb->get_var("SHOW TABLES LIKE '$table_name'") != $table_name) {
            echo '<p>Importer has not been run yet. The log table will be created on first activation.</p>';
            return;
        }

        $runs = $wpdb->get_results("SELECT * FROM $table_name ORDER BY run_id DESC LIMIT 5");

        if (empty($runs)) {
            echo '<p>No import jobs have been run yet.</p>';
            return;
        }

        echo '<table class="widefat" style="margin-top: 1em;">';
        echo '<thead><tr><th>Run ID</th><th>File</th><th>Status</th><th>Created</th><th>Updated</th><th>Errors</th><th>Finished</th></tr></thead>';
        echo '<tbody>';

        foreach ($runs as $run) {
            $status_style = 'color: #2271b1;'; // Blue for processing
            if ($run->status === 'completed') {
                $status_style = 'color: #00a32a;'; // Green
            } elseif (strpos($run->status, 'error') !== false || $run->status === 'failed') {
                $status_style = 'color: #d63638;'; // Red
            }

            printf(
                '<tr><td>%d</td><td>%s</td><td style="%s"><strong>%s</strong></td><td>%d</td><td>%d</td><td>%d</td><td>%s</td></tr>',
                esc_html($run->run_id),
                esc_html($run->source_file),
                esc_attr($status_style),
                esc_html(strtoupper($run->status)),
                esc_html($run->products_created),
                esc_html($run->products_updated),
                esc_html($run->error_count),
                esc_html($run->end_time ? $run->end_time : 'In Progress...')
            );
        }
        echo '</tbody></table>';
        echo '<p>Detailed logs are stored in <code>wp-content/uploads/hpi-importer-logs/</code></p>';
    }
}