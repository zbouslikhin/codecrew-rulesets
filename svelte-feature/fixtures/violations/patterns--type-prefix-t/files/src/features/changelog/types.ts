export type TCategory = {
	name: string;
	items: string[];
};

export type TRelease = {
	version: string;
	date: string;
	categories: TCategory[];
};

export type Author = { name: string };
