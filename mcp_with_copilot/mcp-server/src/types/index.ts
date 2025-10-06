export interface MCPRequest {
    id: string;
    method: string;
    params?: any[];
}

export interface MCPResponse {
    id: string;
    result?: any;
    error?: {
        code: number;
        message: string;
    };
}