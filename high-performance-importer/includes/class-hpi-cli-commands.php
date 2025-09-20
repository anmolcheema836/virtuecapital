<?php
if ( ! defined( 'ABSPATH' ) ) exit;

/**
 * WP-CLI Commands for the High-Performance Importer.
 */
class HPI_CLI_Commands {

    /**
     * Starts the product import process.
     *
     * ## OPTIONS
     *
     * --file=<file>
     * : The absolute path to the CSV file to import.
     *
     * [--batch-size=<size>]
     * : The number of rows to process in each batch.
     * ---
     * default: 100
     * ---
     *
     * ## EXAMPLES
     *
     *     wp product-importer start --file=/path/to/your/products.csv
     *     wp product-importer start --file=/path/to/products.csv --batch-size=50
     *
     * @param array $args Positional arguments.
     * @param array $assoc_args Associative arguments.
     */
    public function start( $args, $assoc_args ) {
        $file_path = $assoc_args['file'];
        $batch_size = absint( $assoc_args['batch-size'] );

        if ( ! file_exists( $file_path ) || ! is_readable( $file_path ) ) {
            WP_CLI::error( "File does not exist or is not readable: {$file_path}" );
            return;
        }

        try {
            $importer = new HPI_Importer();
            $total_rows = $importer->schedule_import( $file_path, $batch_size );
            
            if ($total_rows > 0) {
                 WP_CLI::success( "Import successfully scheduled. {$total_rows} products have been queued for processing in the background." );
            } else {
                 WP_CLI::warning( "The CSV file appears to be empty or invalid. No products were scheduled." );
            }

        } catch ( \Exception $e ) {
            WP_CLI::error( "Failed to start importer: " . $e->getMessage() );
        }
    }
}