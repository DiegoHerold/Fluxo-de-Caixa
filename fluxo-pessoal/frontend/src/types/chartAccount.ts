export type AccountNature = "income" | "expense" | "transfer" | "reserve" | "adjustment" | "liability";

export interface ChartAccount {
  id: number;
  code: string;
  name: string;
  parent_id: number | null;
  account_nature: AccountNature;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ChartAccountTree extends ChartAccount {
  children: ChartAccountTree[];
}
