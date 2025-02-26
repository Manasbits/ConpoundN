-- Enable the pgvector extension
create extension if not exists vector;

-- Create the stock info table
create table stock_info (
    id bigserial primary key,
    url varchar not null,
    chunk_number integer not null,
    title varchar not null,
    summary varchar not null,
    content text not null,     -- Added content column
    metadata jsonb not null default '{}'::jsonb,     -- Added metadata column
    embedding vector(1536),     -- OpenAI embeddings are 1536 dimensions
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,

    -- Add a unique constraint to prevent duplicate chunks for the same URL
    unique(url, chunk_number)
);

-- Create an index for better vector similarity search performance
create index on stock_info using ivfflat (embedding vector_cosine_ops);

-- Create an index on metadata for faster filtering
create index idx_stock_info_metadata on stock_info using gin (metadata);

-- Create a function to search for stock info chunks
create function match_stock_info (
    query_embedding vector(1536),
    match_count int default 10,
    filter jsonb DEFAULT '{}'::jsonb
) returns table (
    id bigint,
    url varchar,
    chunk_number integer,
    title varchar,
    summary varchar,
    content text,
    metadata jsonb,
    similarity float
)
language plpgsql
as $$
#variable_conflict use_column
begin
    return query
    select
        id,
        url,
        chunk_number,
        title,
        summary,
        content,
        metadata,
        1 - (stock_info.embedding <=> query_embedding) as similarity
    from stock_info
    where metadata @> filter
    order by stock_info.embedding <=> query_embedding
    limit match_count;
end;
$$;

-- Everything above will work for any PostgreSQL database. The below commands are for Supabase security

-- Enable RLS on the table
alter table stock_info enable row level security;

-- Create a policy that allows anyone to read
create policy "Allow public read access"
    on stock_info
    for select
    to public
    using (true);