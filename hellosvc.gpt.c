// Pre-setup: Register ring buffers and fixed files
io_uring_register_buffers(&ring, buffers, BUFFER_COUNT);
io_uring_register_files(&ring, fixed_files, MAX_FIXED_FILES);

// Prepare the HTTP response in the buffer (e.g., "HTTP/1.1 200 OK\n\nHello World!")
const char* response = "HTTP/1.1 200 OK\n\nHello World!";
size_t response_len = strlen(response);

// Set the buffer before the loop, so it can be reused for every request
memcpy(buffers[BUFFER_ID], response, response_len);  // Assuming BUFFER_ID corresponds to the buffer index

// Submit multishot accept direct SQE with direct FD flag
sqe = io_uring_get_sqe(&ring);
io_uring_prep_multishot_accept_direct(sqe, listen_fd, SOCK_NONBLOCK);
io_uring_sqe_set_data(sqe, ACCEPT_OP);
io_uring_submit(&ring);

// Event loop with batch submission
while (1) {
    // Peek for completed CQEs
    while (io_uring_peek_cqe(&ring, &cqe) == 0) {
        int res = cqe->res;
        int op = (int)io_uring_cqe_get_data(cqe); // Retrieve operation type

        if (res < 0) {
            io_uring_cqe_seen(&ring, cqe);
            continue; // Handle errors
        }

        switch (op) {
            case ACCEPT_OP: {
                // New connection accepted, FD is directly installed
                int client_fd = res;

                // Prepare send operation with zero-copy fixed buffer (using fixed file flag)
                sqe = io_uring_get_sqe(&ring);
                io_uring_prep_send_zc_fixed(sqe, client_fd, buffers[BUFFER_ID], response_len, 0, BUFFER_ID);
                io_uring_sqe_set_flags(sqe, IOSQE_IO_HARDLINK | IOSQE_FIXED_FILE); // Link send to close, use fixed file
                io_uring_sqe_set_data(sqe, SEND_OP);

                // Prepare close SQE, linked to the send SQE (using fixed file flag)
                sqe = io_uring_get_sqe(&ring);
                io_uring_prep_close(sqe, client_fd);
                io_uring_sqe_set_flags(sqe, IOSQE_FIXED_FILE); // Ensure close uses the fixed FD
                io_uring_sqe_set_data(sqe, CLOSE_OP);

                break;
            }

            case SEND_OP:
                // Send completed; no specific action required
                break;

            case CLOSE_OP:
                // Close completed; no specific action required
                break;
        }

        // Mark CQE as seen
        io_uring_cqe_seen(&ring, cqe);
    }

    // Submit SQEs if there is space in the submission queue
    if (io_uring_sq_ready(&ring) > 0) {
        io_uring_submit(&ring);
    }
}

