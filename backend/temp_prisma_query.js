
const { PrismaClient } = require('@prisma/client');

const prisma = new PrismaClient();

async function runQuery() {
    try {
        const result = 
                await prisma.user.upsert({
                    where: { username: 'cmc5f07zk0005ufv05sg91vob' },
                    update: {},
                    create: {
                        username: 'cmc5f07zk0005ufv05sg91vob',
                        password: 'migrated_user',
                        publicKey: null,
                        privateKey: null
                    }
                })
            ;
        console.log(JSON.stringify({ success: true, data: result }));
    } catch (error) {
        console.log(JSON.stringify({ success: false, error: error.message }));
    } finally {
        await prisma.$disconnect();
    }
}

runQuery();
