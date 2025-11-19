db = db.getSiblingDB('eyrie');

// Create application users for authentication
db.users.insertMany([
  {
    username: 'admin',
    email: 'admin@example.com',
    password_hash: 'scrypt:32768:8:1$1TR9bat9iU8i44Td$2d1a2bf32b58a668ae9d38c40f31b22e6001824a3bb4321d9c6385c757b51c1e7d5eab957ba8ed587418d3a3f1e775d1802891ae4369be89ec767063284bcd2e', // admin
    role: 'admin',
    created_date: new Date(),
    is_active: true
  },
  {
    username: 'uploader',
    email: 'uploader@example.com', 
    password_hash: 'scrypt:32768:8:1$iUZugUuxcEmF75SK$dcda9711a2effe5d2dc264c27e9a60e4588467712d69ad1108996f49e1390e4a6fd0b5213a3269afe9e9202af98dab69a39b99f5dbcdbf1557b24cbfd911bdbe', // uploader
    role: 'uploader',
    created_date: new Date(),
    is_active: true
  },
  {
    username: 'user',
    email: 'user@example.com',
    password_hash: 'scrypt:32768:8:1$nyUOuY5iGadkqIMj$83536b2094c6a3fbedcd8abed981deee292118815a0fc5053bfddec90ebf25f065d8d2fde8c725e515c68f33849c6afc8445d2f392944d216b5d89764d2759a8', // user
    role: 'user', 
    created_date: new Date(),
    is_active: true
  }
]);
