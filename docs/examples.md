# Examples

## Basic CRUD API

### Specification

```yaml
# examples/crud-api.yaml
openapi: 3.0.3
info:
  title: Task Manager API
  version: 1.0.0
servers:
  - url: http://localhost:8080
paths:
  /tasks:
    get:
      summary: List tasks
      parameters:
        - name: status
          in: query
          schema:
            type: string
            enum: [pending, done]
      responses:
        "200":
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/Task"
    post:
      summary: Create task
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/TaskInput"
      responses:
        "201":
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Task"
  /tasks/{id}:
    get:
      summary: Get task
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: integer
      responses:
        "200":
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Task"
        "404":
          description: Not found
    patch:
      summary: Update task
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: integer
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/TaskInput"
      responses:
        "200":
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Task"
        "404":
          description: Not found
    delete:
      summary: Delete task
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: integer
      responses:
        "204":
          description: Deleted
        "404":
          description: Not found
components:
  schemas:
    Task:
      type: object
      required: [id, title]
      properties:
        id:
          type: integer
        title:
          type: string
          maxLength: 200
        description:
          type: string
        status:
          type: string
          enum: [pending, done]
          default: pending
        created_at:
          type: string
          format: date-time
        due_date:
          type: string
          format: date
    TaskInput:
      type: object
      required: [title]
      properties:
        title:
          type: string
          maxLength: 200
        description:
          type: string
        status:
          type: string
          enum: [pending, done]
        due_date:
          type: string
          format: date
```

### Usage

```bash
apimock examples/crud-api.yaml --seed 42
```

```bash
# List all tasks
curl http://localhost:8080/tasks

# Filter by status
curl "http://localhost:8080/tasks?status=pending"

# Create task
curl -X POST http://localhost:8080/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Learn ApiMock", "description": "Read the docs"}'

# Get task
curl http://localhost:8080/tasks/1

# Update task
curl -X PATCH http://localhost:8080/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"status": "done"}'

# Delete task
curl -X DELETE http://localhost:8080/tasks/1
```

## E-Commerce API

### Specification

```yaml
# examples/ecommerce.yaml
openapi: 3.0.3
info:
  title: Shop API
  version: 2.0.0
paths:
  /products:
    get:
      summary: List products
      parameters:
        - name: category
          in: query
          schema:
            type: string
        - name: min_price
          in: query
          schema:
            type: number
        - name: max_price
          in: query
          schema:
            type: number
      responses:
        "200":
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/Product"
  /products/{id}:
    get:
      summary: Get product
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        "200":
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Product"
  /categories:
    get:
      summary: List categories
      responses:
        "200":
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/Category"
  /cart:
    get:
      summary: Get cart
      responses:
        "200":
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Cart"
    post:
      summary: Add to cart
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/CartItemInput"
      responses:
        "200":
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Cart"
  /orders:
    post:
      summary: Create order
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/OrderInput"
      responses:
        "201":
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Order"
components:
  schemas:
    Product:
      type: object
      required: [id, name, price, category]
      properties:
        id:
          type: string
          format: uuid
        name:
          type: string
        description:
          type: string
        price:
          type: number
          minimum: 0
        category:
          type: string
        in_stock:
          type: boolean
          default: true
        tags:
          type: array
          items:
            type: string
    Category:
      type: object
      required: [id, name]
      properties:
        id:
          type: string
        name:
          type: string
    Cart:
      type: object
      required: [items, total]
      properties:
        items:
          type: array
          items:
            $ref: "#/components/schemas/CartItem"
        total:
          type: number
    CartItem:
      type: object
      required: [product_id, quantity]
      properties:
        product_id:
          type: string
          format: uuid
        quantity:
          type: integer
          minimum: 1
        price:
          type: number
    CartItemInput:
      type: object
      required: [product_id, quantity]
      properties:
        product_id:
          type: string
          format: uuid
        quantity:
          type: integer
          minimum: 1
    Order:
      type: object
      required: [id, items, total, status]
      properties:
        id:
          type: string
          format: uuid
        items:
          type: array
          items:
            $ref: "#/components/schemas/OrderItem"
        total:
          type: number
        status:
          type: string
          enum: [pending, confirmed, shipped, delivered]
        created_at:
          type: string
          format: date-time
    OrderItem:
      type: object
      required: [product_id, quantity, price]
      properties:
        product_id:
          type: string
          format: uuid
        quantity:
          type: integer
        price:
          type: number
    OrderInput:
      type: object
      required: [items]
      properties:
        items:
          type: array
          items:
            $ref: "#/components/schemas/OrderItemInput"
    OrderItemInput:
      type: object
      required: [product_id, quantity]
      properties:
        product_id:
          type: string
          format: uuid
        quantity:
          type: integer
          minimum: 1
```

## Blog API

### Specification

```yaml
# examples/blog.yaml
openapi: 3.0.3
info:
  title: Blog API
  version: 1.0.0
paths:
  /posts:
    get:
      summary: List posts
      parameters:
        - name: tag
          in: query
          schema:
            type: string
        - name: limit
          in: query
          schema:
            type: integer
            default: 10
      responses:
        "200":
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/PostSummary"
    post:
      summary: Create post
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/PostInput"
      responses:
        "201":
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Post"
  /posts/{slug}:
    get:
      summary: Get post
      parameters:
        - name: slug
          in: path
          required: true
          schema:
            type: string
      responses:
        "200":
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Post"
        "404":
          description: Not found
  /tags:
    get:
      summary: List tags
      responses:
        "200":
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/Tag"
components:
  schemas:
    Post:
      type: object
      required: [id, slug, title, content, author, published_at, tags]
      properties:
        id:
          type: integer
        slug:
          type: string
          pattern: "^[a-z0-9-]+$"
        title:
          type: string
        content:
          type: string
        excerpt:
          type: string
        author:
          $ref: "#/components/schemas/Author"
        published_at:
          type: string
          format: date-time
        tags:
          type: array
          items:
            $ref: "#/components/schemas/Tag"
    PostSummary:
      type: object
      required: [id, slug, title, excerpt, author, published_at, tags]
      properties:
        id:
          type: integer
        slug:
          type: string
        title:
          type: string
        excerpt:
          type: string
        author:
          $ref: "#/components/schemas/Author"
        published_at:
          type: string
          format: date-time
        tags:
          type: array
          items:
            $ref: "#/components/schemas/Tag"
    PostInput:
      type: object
      required: [title, content, tags]
      properties:
        title:
          type: string
        content:
          type: string
        tags:
          type: array
          items:
            type: string
    Author:
      type: object
      required: [id, name, email]
      properties:
        id:
          type: integer
        name:
          type: string
        email:
          type: string
          format: email
        bio:
          type: string
        avatar_url:
          type: string
          format: uri
    Tag:
      type: object
      required: [id, name]
      properties:
        id:
          type: integer
        name:
          type: string
```

## Running Examples

```bash
# CRUD API
apimock examples/crud-api.yaml --seed 42

# E-Commerce
apimock examples/ecommerce.yaml --seed 123 --port 9000

# Blog
apimock examples/blog.yaml --seed 999 --delay 100
```

## JSON Specifications

All examples also available as JSON. Convert with:

```bash
# YAML to JSON
python -c "import yaml, json; print(json.dumps(yaml.safe_load(open('crud-api.yaml')), indent=2))" > crud-api.json
```