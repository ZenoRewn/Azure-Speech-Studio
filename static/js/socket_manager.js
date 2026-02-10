/**
 * SocketIO connection manager.
 */
const SocketManager = (() => {
  let socket = null;

  function connect() {
    if (socket) return socket;

    socket = io({
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionAttempts: 10,
      reconnectionDelay: 1000,
    });

    socket.on('connect', () => {
      console.log('SocketIO connected:', socket.id);
    });

    socket.on('disconnect', (reason) => {
      console.log('SocketIO disconnected:', reason);
    });

    socket.on('connect_error', (err) => {
      console.error('SocketIO connection error:', err);
    });

    return socket;
  }

  function getSocket() {
    if (!socket) connect();
    return socket;
  }

  return { connect, getSocket };
})();

// Create connection immediately (scripts are at end of body, DOM is ready)
SocketManager.connect();
