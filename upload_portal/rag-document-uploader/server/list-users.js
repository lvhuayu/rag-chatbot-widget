const { PrismaClient } = require('@prisma/client');

const prisma = new PrismaClient();

async function listUsers() {
    try {
        console.log('Fetching registered users...\n');
        
        const users = await prisma.user.findMany({
            select: {
                id: true,
                username: true,
                createdAt: true,
                _count: {
                    select: {
                        documents: true
                    }
                }
            },
            orderBy: {
                createdAt: 'desc'
            }
        });

        if (users.length === 0) {
            console.log('No users found in the database.');
            return;
        }

        console.log(`Found ${users.length} user(s):\n`);
        
        users.forEach((user, index) => {
            console.log(`${index + 1}. Username: ${user.username}`);
            console.log(`   ID: ${user.id}`);
            console.log(`   Created: ${user.createdAt.toLocaleString()}`);
            console.log(`   Documents: ${user._count.documents}`);
            console.log('');
        });

    } catch (error) {
        console.error('Error fetching users:', error);
    } finally {
        await prisma.$disconnect();
    }
}

listUsers(); 