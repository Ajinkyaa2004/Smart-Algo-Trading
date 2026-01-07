import { useState, useEffect } from 'react';
import { useCombobox } from 'downshift';
import { Search, Loader2, Check } from 'lucide-react';
import { cn } from '../lib/utils';

interface SymbolSearchProps {
    value: string;
    onChange: (value: string) => void;
    exchange: string;
    placeholder?: string;
    className?: string;
}

export function SymbolSearch({ value, onChange, exchange, placeholder, className }: SymbolSearchProps) {
    const [items, setItems] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);

    const fetchSuggestions = async (inputValue: string) => {
        if (!inputValue || inputValue.length < 2) {
            setItems([]);
            return;
        }

        setLoading(true);
        try {
            // Use the general search endpoint which supports filtering by exchange
            const response = await fetch(`http://localhost:8000/api/market/instruments/search/${inputValue}?exchange=${exchange}`);
            if (response.ok) {
                const data = await response.json();
                if (data.status === 'success') {
                    setItems(data.results || []);
                }
            }
        } catch (error) {
            console.error('Failed to fetch suggestions:', error);
        } finally {
            setLoading(false);
        }
    };

    const {
        isOpen,
        getMenuProps,
        getInputProps,
        highlightedIndex,
        getItemProps,
        setInputValue,
    } = useCombobox({
        items,
        itemToString: (item) => (item ? item.tradingsymbol : ''),
        onInputValueChange: ({ inputValue }) => {
            fetchSuggestions(inputValue || '');
            onChange(inputValue || ''); // Update parent state directly on input
        },
        onSelectedItemChange: ({ selectedItem }) => {
            if (selectedItem) {
                onChange(selectedItem.tradingsymbol);
            }
        },
        initialInputValue: value,
    });

    // Sync internal input value if prop changes externally (e.g., when switching tabs)
    useEffect(() => {
        setInputValue(value);
    }, [value, setInputValue]);

    return (
        <div className={cn("relative w-full", className)}>
            <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-500" />
                <input
                    {...getInputProps()}
                    className="w-full pl-9 pr-4 py-2 bg-zinc-900 border border-zinc-800 text-zinc-100 placeholder-zinc-500 rounded-md focus:ring-blue-500 focus:border-blue-500 transition-all font-mono uppercase"
                    placeholder={placeholder || "Search Symbol"}
                />
                {loading && (
                    <div className="absolute right-3 top-1/2 -translate-y-1/2">
                        <Loader2 className="h-4 w-4 animate-spin text-zinc-500" />
                    </div>
                )}
            </div>

            <ul
                {...getMenuProps()}
                className={cn(
                    "absolute z-50 w-full mt-1 bg-zinc-900 border border-zinc-800 rounded-md shadow-xl max-h-60 overflow-auto scrollbar-hide py-1",
                    !isOpen || items.length === 0 ? "hidden" : ""
                )}
            >
                {isOpen &&
                    items.map((item, index) => (
                        <li
                            key={`${item.tradingsymbol}-${index}`}
                            {...getItemProps({ item, index })}
                            className={cn(
                                "px-4 py-2 text-sm cursor-pointer flex flex-col gap-0.5",
                                highlightedIndex === index ? "bg-blue-600/20 text-blue-100" : "text-zinc-300 hover:bg-zinc-800"
                            )}
                        >
                            <div className="flex items-center justify-between">
                                <span className="font-bold">{item.tradingsymbol}</span>
                                <span className="text-xs text-zinc-500">{item.exchange}</span>
                            </div>
                            <span className="text-xs text-zinc-500 truncate">{item.name}</span>
                        </li>
                    ))}
            </ul>
        </div>
    );
}
