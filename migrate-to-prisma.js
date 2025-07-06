#!/usr/bin/env node
/**
 * Migration script to consolidate SQLite RAG database into Prisma database
 */

const { PrismaClient } = require('@prisma/client');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const fs = require('fs');

const prisma = new PrismaClient();
const RAG_DB_PATH = path.join(__dirname, 'backend', 'rag_database.db');

async function migrateRAGData() {
    console.log('🔄 Starting RAG data migration to Prisma...');
    
    try {
        // Check if RAG database exists
        if (!fs.existsSync(RAG_DB_PATH)) {
            console.log('⚠️  RAG database not found, skipping migration');
            return;
        }

        // Connect to SQLite RAG database
        const ragDb = new sqlite3.Database(RAG_DB_PATH);
        
        // Get all documents from RAG database
        const documents = await new Promise((resolve, reject) => {
            ragDb.all(`
                SELECT id, url, title, content, timestamp, user_id
                FROM documents
                ORDER BY timestamp DESC
            `, (err, rows) => {
                if (err) reject(err);
                else resolve(rows);
            });
        });

        console.log(`📄 Found ${documents.length} documents to migrate`);

        // Get all embeddings from RAG database
        const embeddings = await new Promise((resolve, reject) => {
            ragDb.all(`
                SELECT id, document_id, embedding_data, embedding_dimension
                FROM embeddings
            `, (err, rows) => {
                if (err) reject(err);
                else resolve(rows);
            });
        });

        console.log(`🧠 Found ${embeddings.length} embeddings to migrate`);

        // Create a map of embeddings by document_id
        const embeddingMap = new Map();
        embeddings.forEach(emb => {
            embeddingMap.set(emb.document_id, {
                embeddingData: emb.embedding_data,
                embeddingDimension: emb.embedding_dimension
            });
        });

        // Migrate each document
        let migratedCount = 0;
        let skippedCount = 0;

        for (const doc of documents) {
            try {
                // Check if user exists, create if not
                let user = await prisma.user.findFirst({
                    where: { username: doc.user_id }
                });

                if (!user) {
                    user = await prisma.user.create({
                        data: {
                            username: doc.user_id,
                            password: 'migrated_user', // Default password for migrated users
                            publicKey: null,
                            privateKey: null
                        }
                    });
                    console.log(`👤 Created user: ${doc.user_id}`);
                }

                // Check if RAG document already exists
                const existingDoc = await prisma.rAGDocument.findFirst({
                    where: {
                        title: doc.title,
                        userId: user.id
                    }
                });

                if (existingDoc) {
                    console.log(`⏭️  Skipping existing document: ${doc.title} (User: ${doc.user_id})`);
                    skippedCount++;
                    continue;
                }

                // Create RAG document
                const ragDocument = await prisma.rAGDocument.create({
                    data: {
                        id: doc.id, // Use original ID to maintain references
                        userId: user.id,
                        url: doc.url,
                        title: doc.title,
                        content: doc.content,
                        timestamp: new Date(doc.timestamp),
                        createdAt: new Date(doc.timestamp)
                    }
                });

                // Create embedding if exists
                const embedding = embeddingMap.get(doc.id);
                if (embedding) {
                    await prisma.rAGEmbedding.create({
                        data: {
                            documentId: ragDocument.id,
                            embeddingData: embedding.embeddingData,
                            embeddingDimension: embedding.embeddingDimension
                        }
                    });
                }

                console.log(`✅ Migrated document: ${doc.title} (User: ${doc.user_id})`);
                migratedCount++;

            } catch (error) {
                console.error(`❌ Error migrating document ${doc.title}:`, error.message);
            }
        }

        // Close SQLite connection
        ragDb.close();

        console.log('\n📊 Migration Summary:');
        console.log(`   ✅ Migrated: ${migratedCount} documents`);
        console.log(`   ⏭️  Skipped: ${skippedCount} documents (already exist)`);
        console.log(`   🧠 Embeddings: ${embeddingMap.size} migrated`);

        // Verify migration
        const totalRAGDocs = await prisma.rAGDocument.count();
        const totalEmbeddings = await prisma.rAGEmbedding.count();
        
        console.log('\n🔍 Verification:');
        console.log(`   📄 Total RAG documents in Prisma: ${totalRAGDocs}`);
        console.log(`   🧠 Total embeddings in Prisma: ${totalEmbeddings}`);

    } catch (error) {
        console.error('❌ Migration failed:', error);
        throw error;
    }
}

async function main() {
    try {
        await migrateRAGData();
        console.log('\n🎉 Migration completed successfully!');
    } catch (error) {
        console.error('💥 Migration failed:', error);
        process.exit(1);
    } finally {
        await prisma.$disconnect();
    }
}

if (require.main === module) {
    main();
}

module.exports = { migrateRAGData }; 