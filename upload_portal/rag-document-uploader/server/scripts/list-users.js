const { PrismaClient } = require('@prisma/client');
const prisma = new PrismaClient();

async function main() {
  const users = await prisma.user.findMany();
  if (users.length === 0) {
    console.log('No users found.');
    return;
  }
  console.log('Users in the uploader portal database:');
  users.forEach(user => {
    console.log(`- id: ${user.id}, username: ${user.username}, createdAt: ${user.createdAt}`);
  });
}

main()
  .catch(e => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  }); 