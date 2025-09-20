<?php
if ( ! defined( 'ABSPATH' ) ) exit;

class HPI_Importer {

    private $logger;
    private $run_id;

    public function __construct() {
        $this->logger = new HPI_Logger();
        // This hook is the entry point for our background processor
        add_action( 'hpi_process_import_batch', [ $this, 'process_batch' ], 10, 2 );
        add_action( 'hpi_finish_import', [ $this, 'finish_import' ], 10, 1 );
    }

    /**
     * Reads a CSV file and schedules batches for background processing.
     *
     * @param string $file_path Absolute path to the CSV file.
     * @param int $batch_size Number of rows per batch.
     * @return int Total number of rows scheduled.
     */
    public function schedule_import( $file_path, $batch_size = 100 ) {
        // Step 1: Initialize a new log entry for this run
        $this->run_id = $this->logger->start_run( $file_path );
        
        $handle = fopen( $file_path, 'r' );
        if ( ! $handle ) {
            throw new \Exception( 'Could not open CSV file.' );
        }

        $header = fgetcsv( $handle ); // Assume first row is header
        $batch = [];
        $row_count = 0;
        $total_rows = 0;

        // Step 2: Read the file line-by-line and create batches
        while ( ( $row = fgetcsv( $handle ) ) !== false ) {
            $batch[] = array_combine( $header, $row ); // Combine header with row
            $row_count++;
            $total_rows++;

            if ( $row_count >= $batch_size ) {
                $this->schedule_batch( $batch );
                $batch = [];
                $row_count = 0;
            }
        }

        // Schedule any remaining rows
        if ( ! empty( $batch ) ) {
            $this->schedule_batch( $batch );
        }

        fclose( $handle );
        
        // Step 3: Schedule a final action to wrap things up
        as_enqueue_async_action( 'hpi_finish_import', [ 'run_id' => $this->run_id ] );
        
        $this->logger->update_run_meta($this->run_id, 'total_rows', $total_rows);

        return $total_rows;
    }
    
    /**
     * Enqueues a single batch of products using Action Scheduler.
     *
     * @param array $batch The data for the products in this batch.
     */
    private function schedule_batch( array $batch ) {
        if ( ! function_exists( 'as_enqueue_async_action' ) ) {
            $this->logger->log( $this->run_id, 'Action Scheduler not found. Cannot schedule batch.', 'critical' );
            return;
        }
        as_enqueue_async_action( 'hpi_process_import_batch', [ 'batch' => $batch, 'run_id' => $this->run_id ] );
    }

    /**
     * Processes a single batch of products. This runs in the background.
     *
     * @param array $batch The product data.
     * @param int $run_id The ID of the current import run.
     */
    public function process_batch( $batch, $run_id ) {
        $stats = ['created' => 0, 'updated' => 0, 'skipped' => 0, 'errors' => 0];

        foreach ( $batch as $row ) {
            try {
                // Ensure SKU exists, as it's our primary key
                if ( empty( $row['sku'] ) ) {
                    $this->logger->log( $run_id, 'Skipping row. Reason: Missing SKU.', 'warning', $row );
                    $stats['skipped']++;
                    continue;
                }

                // Check if product exists
                $product_id = wc_get_product_id_by_sku( $row['sku'] );
                $product = $product_id ? wc_get_product( $product_id ) : new WC_Product_Simple();

                if ( ! $product ) {
                    // If wc_get_product fails for an existing ID
                    $product = new WC_Product_Simple();
                }

                // Set properties
                $product->set_sku( sanitize_text_field($row['sku']) );
                $product->set_name( sanitize_text_field($row['name']) );
                $product->set_description( wp_kses_post($row['description']) );
                $product->set_regular_price( floatval($row['price']) );
                $product->set_manage_stock( true );
                $product->set_stock_quantity( intval($row['stock']) );
                
                // Add categories
                if (!empty($row['categories'])) {
                    $this->set_product_categories($product, $row['categories']);
                }

                // Save product and get ID
                $new_product_id = $product->save();

                // Handle images after we have a product ID
                if ($new_product_id && !empty($row['images'])) {
                     $this->set_product_images($product, $row['images']);
                     $product->save(); // Save again to store image changes
                }
                
                if ( $product_id ) {
                    $stats['updated']++;
                } else {
                    $stats['created']++;
                }

            } catch ( \Exception $e ) {
                $stats['errors']++;
                $this->logger->log( $run_id, "Error processing SKU {$row['sku']}: " . $e->getMessage(), 'error', $row );
            }
        }
        
        // Update the central log with the stats from this batch
        $this->logger->update_run_stats( $run_id, $stats );
    }

    /**
     * Finalizes the import run, sends notifications.
     *
     * @param int $run_id The ID of the import run to finalize.
     */
    public function finish_import( $run_id ) {
        $this->logger->end_run( $run_id );
        $this->logger->send_notification( $run_id );
    }
    
    /**
     * Helper to set product categories, creating them if they don't exist.
     */
    private function set_product_categories( &$product, $categories_str ) {
        $cat_names = array_map('trim', explode('|', $categories_str)); // Allow multiple categories, separated by |
        $term_ids = [];
        foreach($cat_names as $cat_name) {
            $term = get_term_by('name', $cat_name, 'product_cat');
            if (!$term) {
                $term_data = wp_insert_term($cat_name, 'product_cat');
                if (!is_wp_error($term_data)) {
                    $term_ids[] = $term_data['term_id'];
                }
            } else {
                $term_ids[] = $term->term_id;
            }
        }
        if (!empty($term_ids)) {
            $product->set_category_ids($term_ids);
        }
    }
    
    /**
     * Helper to download and attach images to a product.
     */
    private function set_product_images(&$product, $images_str) {
        require_once(ABSPATH . 'wp-admin/includes/media.php');
        require_once(ABSPATH . 'wp-admin/includes/file.php');
        require_once(ABSPATH . 'wp-admin/includes/image.php');
    
        $image_urls = array_map('trim', explode('|', $images_str));
        $gallery_ids = [];
        $product_id = $product->get_id();

        foreach ($image_urls as $index => $url) {
            // Check if image already exists by URL to prevent duplicates
            $attachment_id = attachment_url_to_postid($url);
            if (!$attachment_id) {
                 // Sideload the image
                $attachment_id = media_handle_sideload(['tmp_name' => download_url($url), 'name' => basename($url)], $product_id);
            }
           
            if (!is_wp_error($attachment_id)) {
                if ($index === 0) {
                    $product->set_image_id($attachment_id); // Set featured image
                } else {
                    $gallery_ids[] = $attachment_id;
                }
            }
        }
        if (!empty($gallery_ids)) {
            $product->set_gallery_image_ids($gallery_ids);
        }
    }
}