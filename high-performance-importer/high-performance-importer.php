<?php
/**
 * Plugin Name:       High-Performance Importer
 * Plugin URI:        https://example.com/
 * Description:       A battle-tested, high-performance product importer for WooCommerce handling 100k+ SKUs via WP-CLI.
 * Version:           1.0.0
 * Author:            Anmol Singh
 * Author URI:        https://example.com/
 * License:           GPL v2 or later
 * License URI:       https://www.gnu.org/licenses/gpl-2.0.html
 * Text Domain:       hpi
 * WC requires at least: 8.0
 * WC tested up to:   8.x
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit; // Exit if accessed directly.
}

define( 'HPI_VERSION', '1.0.0' );
define( 'HPI_PLUGIN_DIR', plugin_dir_path( __FILE__ ) );

/**
 * The main function to run the plugin.
 */
function hpi_run_importer_plugin() {
    // Ensure WooCommerce and WP-CLI are active/available
    if ( ! class_exists( 'WooCommerce' ) ) {
        add_action( 'admin_notices', function() {
            echo '<div class="error"><p><strong>High-Performance Importer:</strong> WooCommerce must be activated for this plugin to work.</p></div>';
        });
        return;
    }

    require_once HPI_PLUGIN_DIR . 'includes/class-hpi-logger.php';
    require_once HPI_PLUGIN_DIR . 'includes/class-hpi-importer.php';
    require_once HPI_PLUGIN_DIR . 'includes/class-hpi-admin.php';

    // Register WP-CLI command only if WP-CLI is running
    if ( defined( 'WP_CLI' ) && WP_CLI ) {
        require_once HPI_PLUGIN_DIR . 'includes/class-hpi-cli-commands.php';
        WP_CLI::add_command( 'product-importer', 'HPI_CLI_Commands' );
    }

    // Initialize Admin UI
    new HPI_Admin();
}
add_action( 'plugins_loaded', 'hpi_run_importer_plugin' );

/**
 * Create custom database table on plugin activation.
 */
register_activation_hook( __FILE__, function() {
    require_once HPI_PLUGIN_DIR . 'includes/class-hpi-logger.php';
    HPI_Logger::create_log_table();
} );