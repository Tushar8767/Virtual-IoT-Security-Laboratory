// MongoDB initialization script
// This runs when the MongoDB container is first created.

db = db.getSiblingDB('iot_security_lab');

// Create collections with validation will happen via the application.
// This script just ensures the database exists.
print('MongoDB initialized: iot_security_lab database ready.');
